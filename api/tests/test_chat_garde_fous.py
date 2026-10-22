"""Série 10 : deux garde-fous de la réponse directe du pré-audit — un foyer connecté sans calcul de
puissance est invité au pré-audit (jamais une puissance inventée), et les autres puissances
(compteur, solaire, recharge, froid) ne sont jamais comparées à la plage de PAC. Aucun appel au LLM."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.services import audit_reference as ref
from app.services import rag
from tests.test_chat_reponse_preaudit import DATE, FIOUL, _flux, _sans_reseau

TX = ref.TEXTES_PUISSANCE
with open("tests/fixtures/audit_v25/fioul_6_pieces.json", encoding="utf-8") as f:
    V25 = json.load(f)


# --- Sans bloc puissance ----------------------------------------------------------------------

@pytest.mark.parametrize("question", ["Quelle puissance de pompe à chaleur pour ma maison ?",
                                      "Mes radiateurs suffiront-ils ?", "Un devis à 14 kW, c'est normal ?",
                                      "Combien de kWh représente mon fioul ?"])
def test_audit_ancien_invitation_a_refaire(question):
    attendu = TX["chat_preaudit_ancien"].format(date="22/10/2026")
    assert rag.reponse_preaudit(V25, DATE, question, connecte=True) == attendu
    assert "{" not in attendu


def test_aucun_preaudit_invitation_a_le_faire():
    assert rag.reponse_preaudit(None, None, "Quelle puissance de pompe à chaleur ?", connecte=True) == \
        TX["chat_sans_preaudit"]


def test_visiteur_sans_compte_voie_habituelle():
    assert rag.reponse_preaudit(None, None, "Quelle puissance de pompe à chaleur ?") is None
    assert rag.reponse_preaudit(V25, DATE, "Quelle puissance de pompe à chaleur ?") is None


def test_hors_sujet_toujours_au_llm_meme_connecte():
    assert rag.reponse_preaudit(None, None, "Quelle marque de PAC choisir ?", connecte=True) is None
    assert rag.reponse_preaudit(V25, DATE, "Combien coûte une pompe à chaleur ?", connecte=True) is None


# --- Les autres puissances ------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Quelle puissance souscrire au compteur ?", "Quelle puissance de panneaux solaires pour ma maison ?",
    "Combien de kWc pour mon toit ?", "Un onduleur de 5 kW, c'est bien ?", "Une batterie de 5 kW ?",
    "Une borne de 7 kW, c'est assez ?", "Quelle puissance de recharge pour ma voiture ?",
    "Une clim de 3,5 kW pour ma chambre ?", "Un split de 2,5 kW ?",
])
def test_les_autres_puissances_ne_sont_jamais_comparees_a_la_pac(question):
    assert not {"puissance", "devis"} & set(rag.sujets_preaudit(question))
    assert rag.reponse_preaudit(FIOUL, DATE, question, connecte=True) is None
    assert rag.reponse_preaudit(None, None, question, connecte=True) is None


def test_radiateurs_et_releve_restent_intacts():
    assert rag.sujets_preaudit("Mes radiateurs et ma batterie ?") == ["radiateurs"]
    assert rag.sujets_preaudit("Mon relevé de fioul et la clim ?") == ["releve"]


# --- Par la route, contre la base de dev -------------------------------------------------

@pytest.fixture(scope="module")
def foyers():
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
        ids = {}
        async with async_session() as s:
            for cle in ("v25", "sans"):
                u = User(email=f"s10-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
                s.add(u)
                await s.flush()
                h = House(user_id=u.id, code_postal="13001", chauffage_principal="fioul")
                s.add(h)
                await s.flush()
                if cle == "v25":
                    s.add(Audit(house_id=h.id, json_result=V25, version_helios="v2.5"))
                ids[cle] = u.id
            await s.commit()
        return ids

    async def effacer(ids):
        async with async_session() as s:
            for uid in ids.values():
                for sql in ("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = :u)",
                            "DELETE FROM conversations WHERE user_id = :u",
                            "DELETE FROM audits WHERE house_id = (SELECT id FROM houses WHERE user_id = :u)",
                            "DELETE FROM houses WHERE user_id = :u", "DELETE FROM users WHERE id = :u"):
                    await s.execute(text(sql), {"u": uid})
            await s.commit()

    with TestClient(app) as client:
        if not client.portal.call(pret):
            pytest.skip("Postgres de développement absent")
        ids = client.portal.call(creer)
        try:
            yield client, {k: {"Authorization": f"Bearer {create_access_token(str(v))}"} for k, v in ids.items()}
        finally:
            client.portal.call(lambda: effacer(ids))
            client.portal.call(engine.dispose)


def _interdire_llm(monkeypatch):
    from app.services import router_llm

    async def interdit(*a, **k):
        raise AssertionError("le LLM ne doit pas être appelé")
    monkeypatch.setattr(router_llm, "generate_route", interdit)


def _texte(evs):
    return "".join(e["text"] for e in evs if e["type"] == "token")


@pytest.mark.parametrize("foyer, cle", [("v25", "chat_preaudit_ancien"), ("sans", "chat_sans_preaudit")])
def test_la_route_invite_au_preaudit_sans_llm(foyers, monkeypatch, foyer, cle):
    c, h = foyers
    _sans_reseau(monkeypatch)
    _interdire_llm(monkeypatch)
    evs = _flux(c.post("/api/chat/messages", headers=h[foyer],
                       json={"content": "Quelle puissance de pompe à chaleur pour ma maison ?"}))
    texte = _texte(evs)
    assert texte.startswith(TX[cle].split("{")[0]) and "{" not in texte
    assert evs[0]["instant"] is True


def test_le_visiteur_sans_compte_va_au_llm(foyers, monkeypatch):
    from app.services import router_llm
    c, _ = foyers
    _sans_reseau(monkeypatch)
    appels = []

    async def faux(*a, **k):
        appels.append(1)

        async def flux():
            yield "ok"
        return "local", False, flux()
    monkeypatch.setattr(router_llm, "generate_route", faux)
    c.post("/api/chat/messages", json={"content": "Quelle puissance de pompe à chaleur pour ma maison ?"})
    assert appels == [1]
