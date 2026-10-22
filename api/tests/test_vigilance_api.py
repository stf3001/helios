"""Vigilance météo par l'API : un foyer du Var la voit, un foyer du Nord non — contre la base de dev.

Les épisodes sont posés en base relativement à maintenant (comme après une collecte) ; aucun appel
réseau. Tout est effacé en fin de module.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.user import User
from app.models.vigilance import VigilanceDepartement
from app.routers.chat import _carnet_du_foyer

DEP = "48"  # absent de la fixture simulée : une collecte de dev chargée ne fausse pas le test


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM vigilance_departements LIMIT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0042 non appliquée")
        maintenant = datetime.now(timezone.utc)

        async def creer():
            async with async_session() as s:
                await s.execute(text("DELETE FROM vigilance_departements WHERE departement = :d"), {"d": DEP})
                ids = {}
                for cle, cp in (("var", "48000"), ("nord", "59000")):
                    u = User(email=f"vigi-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
                    s.add(u)
                    await s.flush()
                    s.add(House(user_id=u.id, code_postal=cp, type_logement="maison", statut="proprietaire"))
                    ids[cle] = u.id
                eps = [
                    VigilanceDepartement(departement=DEP, phenomene="vent", couleur="orange",
                                         debut=maintenant - timedelta(hours=1), fin=maintenant + timedelta(hours=6),
                                         collecte_le=maintenant),
                    VigilanceDepartement(departement=DEP, phenomene="orages", couleur="orange",
                                         debut=maintenant - timedelta(days=2), fin=maintenant - timedelta(days=1),
                                         collecte_le=maintenant),
                ]
                s.add_all(eps)
                await s.flush()
                ids["episodes"] = [e.id for e in eps]
                await s.commit()
                return ids

        async def effacer(ids):
            async with async_session() as s:
                await s.execute(text("DELETE FROM vigilance_departements WHERE id = ANY(:i)"), {"i": ids["episodes"]})
                for cle in ("var", "nord"):
                    await s.execute(text("DELETE FROM houses WHERE user_id = :u"), {"u": ids[cle]})
                    await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids[cle]})
                await s.commit()
        ids = client.portal.call(creer)
        try:
            yield client, ids, {k: {"Authorization": f"Bearer {create_access_token(str(ids[k]))}"} for k in ("var", "nord")}
        finally:
            client.portal.call(lambda: effacer(ids))
            client.portal.call(engine.dispose)


def test_le_var_voit_la_vigilance_et_le_degat_a_noter(ctx):
    c, _, h = ctx
    r = c.get("/api/houses/me/vigilance", headers=h["var"]).json()
    assert [v["phenomene"] for v in r["actives"]] == ["vent"] and r["actives"][0]["gestes"]
    assert [a["phenomene"] for a in r["apres"]] == ["orages"]
    bloc = c.get("/api/houses/me/a-faire", headers=h["var"]).json()
    assert [v["phenomene"] for v in bloc["vigilances"]] == ["vent"] and bloc["rien_d_urgent"] is False
    assert [a["phenomene"] for a in bloc["apres_episode"]] == ["orages"]


def test_le_nord_ne_voit_rien(ctx):
    c, _, h = ctx
    assert c.get("/api/houses/me/vigilance", headers=h["nord"]).json() == {"actives": [], "apres": []}
    bloc = c.get("/api/houses/me/a-faire", headers=h["nord"]).json()
    assert bloc["vigilances"] == [] and bloc["apres_episode"] == []


def test_le_chat_recoit_la_vigilance_du_departement(ctx):
    c, ids, _ = ctx

    async def carnet():
        async with async_session() as s:
            house = (await s.execute(text("SELECT id FROM houses WHERE user_id = :u"), {"u": ids["var"]})).scalar()
            return await _carnet_du_foyer(s, await s.get(House, house))
    contexte = c.portal.call(carnet)
    assert contexte["vigilance"][0]["phenomene"] == "vent" and contexte["vigilance"][0]["statut"] == "observe"
