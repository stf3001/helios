"""Série 9 : la réponse directe du pré-audit dans le chat — puissance, radiateurs, relevé et
puissance d'un devis, faites des phrases du pré-audit, sans LLM. Aucun appel au LLM ici."""
import json
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.services import audit_reference as ref
from app.services import rag
from app.services.audit_engine import run_audit
from tests.maisons_puissance import maisons, pieces_fioul
from tests.test_audit_engine import AUJOURD_HUI, maison_type

DATE = "2026-10-22T10:00:00+00:00"
INTRO = "D'après votre pré-audit du 22/10/2026 :\n\n"


def resultat(**champs) -> dict:
    pieces, emetteurs = pieces_fioul()
    h = maison_type(**champs)
    return json.loads(json.dumps(run_audit(h, aujourd_hui=AUJOURD_HUI, pieces=pieces, emetteurs=emetteurs), default=str))


FIOUL = resultat()                                          # sans relevé : volume, plage 6 à 9 kW
RELEVE = resultat(conso_autre_energie_type="fioul", conso_autre_energie_qte=1500, conso_autre_energie_unite="litres")


def rep(r, question):
    return rag.reponse_preaudit(r, DATE, question)


# --- Chaque sujet ---------------------------------------------------------------------------

def test_puissance_fourchette_et_plage():
    p = FIOUL["puissance"]
    assert rep(FIOUL, "Quelle puissance de pompe à chaleur pour ma maison ?") == INTRO + p["texte"] + "\n" + p["texte_plage"]


def test_radiateurs_une_ligne_par_piece():
    r = rep(FIOUL, "Mes radiateurs suffiront-ils ?")
    lignes = r.removeprefix(INTRO).split("\n")
    assert lignes == [f"- {x['texte']}" for x in FIOUL["puissance"]["radiateurs"]]
    assert lignes[0] == "- Séjour : vos radiateurs suffisent avec une eau à 55 °C."
    assert lignes[-1] == "- Salle de bains : la puissance des radiateurs n'est pas indiquée ; l'installateur doit la relever."


def test_radiateurs_sans_pieces():
    r = json.loads(json.dumps(run_audit(maison_type(), aujourd_hui=AUJOURD_HUI), default=str))
    assert rep(r, "Mes radiateurs suffiront-ils ?") == INTRO + ref.TEXTES_PUISSANCE["chat_sans_pieces"]


def test_releve_et_eau_chaude():
    assert rep(RELEVE, "Combien de kWh représente mon fioul ?") == \
        INTRO + "Votre relevé (1 500 litres de fioul par an) représente environ 15 000 kWh."
    gaz = resultat(chauffage_principal="gaz", ecs="gaz", nb_occupants=3, conso_autre_energie_type="gaz",
                   conso_autre_energie_qte=12000, conso_autre_energie_unite="kwh")
    assert rep(gaz, "Mon relevé de gaz, ça fait combien ?") == INTRO + (
        "Votre relevé (12 000 kWh de gaz par an) représente environ 12 000 kWh.\n"
        "Environ 3 300 kWh vont à l'eau chaude : le chauffage en garde 8 700 kWh.")
    assert rep(FIOUL, "Combien de kWh représente mon fioul ?") == INTRO + ref.TEXTES_PUISSANCE["chat_sans_releve"]


@pytest.mark.parametrize("question, cle, kw", [
    ("Un installateur me propose 14 kW, c'est normal ?", "chat_devis_dessus", "14"),
    ("Le devis dit 7,5 kw", "chat_devis_dans", "7,5"),
    ("5 kW, c'est assez ?", "chat_devis_dessous", "5"),
])
def test_devis_compare_a_la_plage(question, cle, kw):
    assert rep(FIOUL, question) == INTRO + ref.TEXTES_PUISSANCE[cle].format(kw=kw, pac_bas="6", pac_haut="9")


def test_devis_sans_plage_va_au_llm():
    convecteurs = maisons()["convecteurs"][0]   # PAC air/air : pas de plage air/eau
    r = json.loads(json.dumps(run_audit(convecteurs, aujourd_hui=AUJOURD_HUI), default=str))
    assert r["puissance"]["affichage"] == "puissance"
    assert rep(r, "Un installateur me propose 14 kW, c'est normal ?") is None
    assert rep(r, "Quelle puissance de chauffage pour ma maison ?") == INTRO + r["puissance"]["texte"]


def test_kwh_n_est_pas_un_devis():
    assert rag.sujets_preaudit("Mon relevé fait 15 000 kWh") == ["releve"]


# --- Ce qui reste au LLM --------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Quelle marque de PAC choisir ?", "Combien coûte une pompe à chaleur ?", "Une PAC, c'est bruyant ?",
    "Quelles aides pour une pompe à chaleur ?", "Quelle puissance souscrire au compteur ?",
])
def test_les_questions_generales_restent_au_llm(question):
    assert rep(FIOUL, question) is None


def test_sans_bloc_puissance_rien():
    with open("tests/fixtures/audit_v25/fioul_6_pieces.json", encoding="utf-8") as f:
        v25 = json.load(f)
    assert rep(v25, "Quelle puissance de pompe à chaleur pour ma maison ?") is None


def test_plusieurs_sujets_ordre_fixe_sans_doublon():
    r = rep(RELEVE, "Quelle puissance ? Un devis à 14 kW et 13 kW, et mes radiateurs, et mon fioul ?")
    corps = r.removeprefix(INTRO)
    i_rad, i_rel = corps.index("- Séjour"), corps.index("Votre relevé")
    i_dev, i_pui = corps.index("14 kW, c'est"), corps.index("Au jour le plus froid")
    assert i_rad < i_rel < i_dev < i_pui
    assert corps.count("Au jour le plus froid") == 1 and corps.count("Votre relevé") == 1


@pytest.mark.parametrize("question", ["Quelle puissance de PAC ?", "Mes radiateurs suffiront-ils ?",
                                      "Combien de kWh représente mon fioul ?", "14 kW, c'est normal ?"])
def test_aucune_variable_non_remplie(question):
    for r in (FIOUL, RELEVE):
        assert "{" not in rep(r, question)


# --- Par la route, contre la base de dev -------------------------------------------------

@pytest.fixture(scope="module")
def foyer():
    from app.core.db import async_session, engine
    from app.core.security import create_access_token
    from app.main import app
    from app.models.audit import Audit
    from app.models.house import House
    from app.models.user import User

    async def pret():
        await engine.dispose()
        try:
            async with async_session() as s:
                await s.execute(text("SELECT 1 FROM audits LIMIT 1"))
            return True
        except Exception:
            return False

    async def creer():
        async with async_session() as s:
            u = User(email=f"s9-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
            s.add(u)
            await s.flush()
            h = House(user_id=u.id, code_postal="13001", chauffage_principal="fioul")
            s.add(h)
            await s.flush()
            s.add(Audit(house_id=h.id, json_result=FIOUL, version_helios="v2.7"))
            await s.commit()
            return u.id

    async def effacer(uid):
        async with async_session() as s:
            for sql in ("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = :u)",
                        "DELETE FROM conversations WHERE user_id = :u",
                        "DELETE FROM audits WHERE house_id = (SELECT id FROM houses WHERE user_id = :u)",
                        "DELETE FROM houses WHERE user_id = :u", "DELETE FROM users WHERE id = :u"):
                await s.execute(text(sql), {"u": uid})
            await s.commit()

    with TestClient(app) as client:
        if not client.portal.call(pret):
            pytest.skip("Postgres de développement absent")
        uid = client.portal.call(creer)
        try:
            yield client, {"Authorization": f"Bearer {create_access_token(str(uid))}"}, uid
        finally:
            client.portal.call(lambda: effacer(uid))
            client.portal.call(engine.dispose)


def _sans_reseau(monkeypatch):
    from app.services import ollama_client

    async def embed(_):
        return [0.0] * 1024

    async def chercher(_db, _vec, *a, **k):
        return []

    monkeypatch.setattr(ollama_client, "embed", embed)
    monkeypatch.setattr(rag, "search_chunks", chercher)


def _flux(r):
    return [json.loads(l) for l in r.text.splitlines() if l.strip()]


def test_la_route_repond_sans_llm(foyer, monkeypatch):
    from app.services import admin_stats, router_llm
    c, h, _ = foyer
    _sans_reseau(monkeypatch)

    async def interdit(*a, **k):
        raise AssertionError("le LLM ne doit pas être appelé")
    monkeypatch.setattr(router_llm, "generate_route", interdit)

    evs = _flux(c.post("/api/chat/messages", headers=h, json={"content": "Mes radiateurs suffiront-ils ?"}))
    assert evs[0]["type"] == "conversation" and evs[0]["instant"] is True
    texte = "".join(e["text"] for e in evs if e["type"] == "token")
    assert texte.startswith("D'après votre pré-audit du") and "- Séjour" in texte
    assert evs[-1]["type"] == "message_id"

    from app.core.db import async_session

    async def lire():
        async with async_session() as s:
            m = await s.scalar(text("SELECT model_used FROM messages WHERE id = :i"), {"i": uuid.UUID(evs[-1]["message_id"])})
            stats = await admin_stats.activite_helios(s)
            return m, stats["repartition_7j"]
    model, repartition = c.portal.call(lire)
    assert model == "preaudit" and repartition.get("preaudit", 0) >= 1


def test_force_llm_passe_outre(foyer, monkeypatch):
    from app.services import router_llm
    c, h, _ = foyer
    _sans_reseau(monkeypatch)
    appels = []

    async def faux(*a, **k):
        appels.append(k.get("message"))

        async def flux():
            yield "réponse du modèle"
        return "local", False, flux()
    monkeypatch.setattr(router_llm, "generate_route", faux)
    evs = _flux(c.post("/api/chat/messages", headers=h,
                       json={"content": "Mes radiateurs suffiront-ils ?", "force_llm": True}))
    assert appels and "".join(e["text"] for e in evs if e["type"] == "token") == "réponse du modèle"


def test_une_question_generale_va_au_llm(foyer, monkeypatch):
    from app.services import router_llm
    c, h, _ = foyer
    _sans_reseau(monkeypatch)
    appels = []

    async def faux(*a, **k):
        appels.append(1)

        async def flux():
            yield "ok"
        return "local", False, flux()
    monkeypatch.setattr(router_llm, "generate_route", faux)
    c.post("/api/chat/messages", headers=h, json={"content": "Quelle marque de PAC choisir ?"})
    assert appels == [1]
