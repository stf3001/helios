"""Point 60 et point 64 : partenaires de démonstration et ordre de l'annuaire, CONTRE LA VRAIE BASE.

Les partenaires « Démo … » viennent de `scripts/seed_partenaires_demo.py` ; le module se saute
s'ils ne sont pas semés. Rien n'est créé ni effacé ici : on lit.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.services import propositions as pr


async def _etat():
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            demos = (await s.execute(text("SELECT count(*) FROM partners WHERE demo"))).scalar()
            demo_id = await s.scalar(text("SELECT id FROM users WHERE email = 'demo@helios.fr'"))
            return demos, demo_id
    except Exception:
        return 0, None


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        demos, demo_id = client.portal.call(_etat)
        if not demos or demo_id is None:
            pytest.skip("Base absente, ou partenaires de démonstration non semés")
        client.demo = {"Authorization": f"Bearer {create_access_token(str(demo_id))}"}
        yield client
        client.portal.call(engine.dispose)


def test_l_annuaire_public_est_alphabetique_et_sans_demo(c):
    noms = [p["raison_sociale"] for p in c.get("/api/partners").json()]
    assert noms == sorted(noms)
    assert noms and not any(n.startswith("Démo") for n in noms)


def test_le_compte_de_demo_voit_les_demos(c):
    vus = {p["raison_sociale"] for _ in range(30) for p in
           c.get("/api/leads/propositions", headers=c.demo, params={"metier": "isolation"}).json()["propositions"]}
    assert vus and all(n.startswith("Démo") for n in vus)


def test_seul_un_compte_de_demo_voit_les_demos():
    assert pr.voit_les_demos("demo@helios.fr") and pr.voit_les_demos("Demo@Helios.fr")
    assert not pr.voit_les_demos("quelquun@exemple.fr") and not pr.voit_les_demos(None)
