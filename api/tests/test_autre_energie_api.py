"""Pré-audit lot 7 : la route refuse un couple type-unité qui ne va pas ensemble, en regardant
aussi la fiche enregistrée. CONTRE LA BASE DE DEV (sauté sans elle, ou sans la migration 0043)."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.user import User


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT conso_autre_energie_unite FROM houses LIMIT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def foyer():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0043 non appliquée")

        async def creer():
            async with async_session() as s:
                u = User(email=f"lot7-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
                s.add(u)
                await s.flush()
                s.add(House(user_id=u.id, code_postal="13001", chauffage_principal="fioul"))
                await s.commit()
                return u.id

        async def effacer(uid):
            async with async_session() as s:
                await s.execute(text("DELETE FROM houses WHERE user_id = :u"), {"u": uid})
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
                await s.commit()

        uid = client.portal.call(creer)
        try:
            yield client, {"Authorization": f"Bearer {create_access_token(str(uid))}"}
        finally:
            client.portal.call(lambda: effacer(uid))
            client.portal.call(engine.dispose)


def test_couple_type_unite(foyer):
    c, h = foyer
    r = c.patch("/api/houses/me", headers=h, json={"conso_autre_energie_type": "fioul", "conso_autre_energie_unite": "m3"})
    assert r.status_code == 400
    r = c.patch("/api/houses/me", headers=h, json={"conso_autre_energie_type": "fioul", "conso_autre_energie_qte": 1500,
                                                   "conso_autre_energie_unite": "litres"})
    assert r.status_code == 200 and r.json()["conso_autre_energie_unite"] == "litres"
    # Le type seul change : l'unité enregistrée (litres) ne va pas avec le gaz → refusé, rien de deviné.
    assert c.patch("/api/houses/me", headers=h, json={"conso_autre_energie_type": "gaz"}).status_code == 400
    r = c.patch("/api/houses/me", headers=h, json={"conso_autre_energie_type": "gaz", "conso_autre_energie_unite": "m3"})
    assert r.status_code == 200
    assert c.patch("/api/houses/me", headers=h, json={"conso_autre_energie_type": "propane"}).status_code == 422
