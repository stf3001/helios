"""Risques de la commune : affichage, contexte du chat, cache de 30 jours, panne — SANS RÉSEAU.

La partie « base » tourne contre le Postgres de dev (sautée sans lui) ; Géorisques et
geo.api.gouv.fr y sont remplacés par des fonctions locales.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.user import User
from app.services import carnet_contexte as cc
from app.services import risques_affichage as ra
from app.services import risques_lecture as rl
from app.services.agents_engine import _REPO_ROOT, parse_faq_markdown

LIGNE = SimpleNamespace(code_insee="83063", commune="LA GARDE-FREINET", catnat_30_ans=12, radon_classe=3,
                        zone_sismique=2, ppr=True, url_rapport="https://www.georisques.gouv.fr/x",
                        collecte_le=datetime(2026, 10, 22, tzinfo=timezone.utc),
                        risques=["radon", "feux_de_foret", "argiles", "inondation"])
VERIF = [{"champ": "zone_old", "libelle": "Vérifiez si votre terrain est concerné", "lien": "https://x"}]


def test_chaque_question_citee_existe_mot_pour_mot_dans_la_fiche():
    titres = {e["titre"] for e in parse_faq_markdown(
        (_REPO_ROOT / "helios" / "kb" / "risques_maison.md").read_text(encoding="utf-8"))}
    for q in [*ra.QUESTIONS.values(), ra.Q_GENERALE, ra.Q_FISSURE]:
        assert q in titres, q


def test_la_section_une_ligne_par_risque_dans_l_ordre_et_les_liens_du_carnet():
    maison = SimpleNamespace(commune="La Garde-Freinet", zone_old="ne_sais_pas")
    s = ra.section(LIGNE, maison, VERIF)
    assert [r["code"] for r in s["risques"]] == ["inondation", "argiles", "feux_de_foret", "radon"]
    assert s["risques"][2]["question"].startswith("Ma commune est exposée aux feux de forêt")
    assert s["debroussaillement"] == VERIF[0] and s["fissure"] is not None
    assert "parcelle" in s["mention"] and s["commune"] == "La Garde-Freinet"
    deja = ra.section(LIGNE, SimpleNamespace(commune=None, zone_old="oui"), VERIF)
    assert deja["debroussaillement"] is None
    sans = ra.section(SimpleNamespace(**{**vars(LIGNE), "risques": ["radon"]}), maison, VERIF)
    assert sans["debroussaillement"] is None and sans["fissure"] is None


def test_le_chat_recoit_une_liste_courte_dans_le_plafond():
    r = ra.pour_le_chat(LIGNE)
    assert r == {"liste": "inondation, argiles, feux_de_foret, radon", "statut": "observe", "echelle": "commune"}
    assert len(r["liste"]) < ra.CHAT_MAX and ra.pour_le_chat(None) is None
    tout = SimpleNamespace(risques=list(ra.RISQUES))
    assert len(ra.pour_le_chat(tout)["liste"]) < 200
    carnet = cc.carnet_contexte([], [], [], [], risques=r)
    assert carnet == {"risques": r} and cc.taille(carnet) <= cc.PLAFOND_CARACTERES


# --- Cache et panne, contre la base -------------------------------------------------------------

CODE = "99999"  # code INSEE fictif, propre aux tests


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM risques_commune LIMIT 1"))
        return True
    except Exception:
        return False


def _faux_collecter(appels: list, panne: bool = False):
    async def collecter(code_insee):
        appels.append(code_insee)
        if panne:
            raise RuntimeError("Géorisques ne répond pas")
        return {"commune": "TESTVILLE", "risques": ["argiles"], "url": None, "catnat_30_ans": 2,
                "radon_classe": 1, "zone_sismique": 1, "ppr": False}
    return collecter


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0041 non appliquée")

        async def creer():
            async with async_session() as s:
                await s.execute(text("DELETE FROM risques_commune WHERE code_insee = :c"), {"c": CODE})
                u = User(email=f"risques-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
                s.add(u)
                await s.flush()
                s.add(House(user_id=u.id, code_postal="83680", type_logement="maison", statut="proprietaire"))
                await s.commit()
                return u.id

        async def effacer(uid):
            async with async_session() as s:
                await s.execute(text("DELETE FROM risques_commune WHERE code_insee = :c"), {"c": CODE})
                await s.execute(text("DELETE FROM houses WHERE user_id = :u"), {"u": uid})
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
                await s.commit()
        uid = client.portal.call(creer)
        try:
            yield client, uid, {"Authorization": f"Bearer {create_access_token(str(uid))}"}
        finally:
            client.portal.call(lambda: effacer(uid))
            client.portal.call(engine.dispose)


def test_cache_de_30_jours_puis_rafraichi(ctx):
    c, _, _ = ctx
    appels = []
    t0 = datetime(2026, 10, 22, tzinfo=timezone.utc)

    async def lire(quand, panne=False):
        async with async_session() as s:
            l = await rl.risques_de_la_commune(s, CODE, quand, _faux_collecter(appels, panne))
            return l.risques if l else None
    assert c.portal.call(lambda: lire(t0)) == ["argiles"] and appels == [CODE]
    assert c.portal.call(lambda: lire(t0 + timedelta(days=29))) == ["argiles"] and len(appels) == 1
    assert c.portal.call(lambda: lire(t0 + timedelta(days=31))) == ["argiles"] and len(appels) == 2
    # Panne au moment de rafraîchir : on rend l'ancienne collecte, sans lever.
    assert c.portal.call(lambda: lire(t0 + timedelta(days=70), panne=True)) == ["argiles"] and len(appels) == 3


def test_panne_sans_rien_en_cache_et_le_carnet_s_affiche(ctx, monkeypatch):
    c, uid, h = ctx
    assert c.get("/api/houses/me/risques", headers=h).json() == {"disponible": False, "raison": "commune_absente"}

    async def communes(cp):
        return [{"code_insee": "88888", "nom": "Panneville"}, {"code_insee": CODE, "nom": "Testville"}]
    monkeypatch.setattr(rl, "communes_du_code_postal", communes)
    assert c.put("/api/houses/me/commune", headers=h, json={"code_insee": "12345"}).status_code == 400
    r = c.put("/api/houses/me/commune", headers=h, json={"code_insee": "88888"})
    assert r.json() == {"code_insee": "88888", "commune": "Panneville"}
    assert c.get("/api/houses/me", headers=h).json()["commune"] == "Panneville"

    appels = []
    monkeypatch.setattr(rl.georisques, "collecter", _faux_collecter(appels, panne=True))
    assert c.get("/api/houses/me/risques", headers=h).json() == {"disponible": False, "raison": "indisponible"}
    assert appels == ["88888"]  # le faux collecteur a bien été appelé : aucun appel réseau
    assert c.get("/api/houses/me/a-faire", headers=h).status_code == 200
    assert c.get("/api/houses/me/entretien", headers=h).status_code == 200
    # Changer de code postal efface la commune : elle se rechoisit.
    c.patch("/api/houses/me", headers=h, json={"code_postal": "83990"})
    assert c.get("/api/houses/me", headers=h).json()["code_insee"] is None
