"""Carnet, lot 10 : `GET /cout` et `/charges`, CONTRE LA VRAIE BASE (sauté sans elle)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.audit import Audit
from app.models.house import House
from app.models.user import User
from tests.test_cout_maison import AUDIT


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM charges_maison LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer(avec_audit: bool, **fiche) -> uuid.UUID:
    async with async_session() as s:
        user = User(email=f"lot10-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        house = House(user_id=user.id, code_postal="83000", **fiche)
        s.add(house)
        await s.flush()
        if avec_audit:
            s.add(Audit(house_id=house.id, json_result=AUDIT))
        await s.commit()
        return user.id


async def _effacer(uids) -> None:
    async with async_session() as s:
        for uid in uids:
            h = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
            if h:
                await s.execute(text("DELETE FROM audits WHERE house_id = :h"), {"h": h})
                await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": h})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        await s.commit()


@pytest.fixture(scope="module")
def foyers():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0033 non appliquée")
        uids = {"vide": client.portal.call(_creer_foyer, False),
                "complet": client.portal.call(lambda: _creer_foyer(True, statut="locataire", type_logement="maison",
                                                                   conso_elec_kwh_an=9000, puissance_souscrite="9"))}
        try:
            yield client, {k: {"Authorization": f"Bearer {create_access_token(str(v))}"} for k, v in uids.items()}
        finally:
            client.portal.call(lambda: _effacer(uids.values()))
            client.portal.call(engine.dispose)


def test_maison_vide(foyers):
    c, h = foyers
    r = c.get("/api/houses/me/cout", headers=h["vide"]).json()
    assert r["total_an_eur"] is None and all(p["montant_eur"] is None for p in r["postes"])
    assert r["effet_travaux"] == {"audit": None, "etudes": []}
    assert c.get("/api/houses/me/charges", headers=h["vide"]).json()["assurance_eur_an"] is None


def test_maison_complete(foyers):
    c, h = foyers
    h = h["complet"]
    assert c.put("/api/houses/me/charges", headers=h, json={"assurance_eur_an": -1}).status_code == 422
    r = c.put("/api/houses/me/charges", headers=h, json={"assurance_eur_an": 380, "eau_eur_an": 410})
    assert r.status_code == 200 and r.json()["eau_eur_an"] == 410
    c.post("/api/houses/me/journal", headers=h, json={"date": "2026-01-15", "type": "reparation",
                                                      "titre": "Fuite", "cout_eur": 95})
    r = c.get("/api/houses/me/cout", headers=h).json()
    postes = {p["code"]: p for p in r["postes"]}
    assert "taxe_fonciere" not in postes  # locataire
    assert postes["assurance"]["montant_eur"] == 380 and postes["entretien"]["montant_eur"] == 95
    # Le plan du pré-audit stocké, identique.
    assert [a["cout_eur"] for a in r["effet_travaux"]["audit"]["actions"]] == [p["cout_eur"] for p in AUDIT["priorites"]]
    assert [a["economie_annuelle_eur"] for a in r["effet_travaux"]["audit"]["actions"]] == [
        p["economie_annuelle_eur"] for p in AUDIT["priorites"]]
    # Le PUT remplace l'ensemble : ce qui n'est pas renvoyé redevient « non renseigné ».
    c.put("/api/houses/me/charges", headers=h, json={"assurance_eur_an": 380})
    assert c.get("/api/houses/me/charges", headers=h).json()["eau_eur_an"] is None
