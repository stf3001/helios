"""Carnet, lot 7 : la fiche suit l'équipement relié, par l'API, CONTRE LA VRAIE BASE.

Même dispositif que `test_carnet_api.py` : un foyer jetable, effacé en fin de module, et le
module se SAUTE ENTIÈREMENT sans le Postgres de développement.

Ce qui est vérifié : création, modification, remplacement, hors service et suppression font
suivre la fiche et son score ; un second équipement en service sur la même origine répond
409 ; `PATCH /houses/me` refuse un champ verrouillé qui CHANGE, accepte la même valeur.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.user import User


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM equipements LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer() -> uuid.UUID:
    async with async_session() as s:
        user = User(email=f"lot7-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        s.add(House(user_id=user.id, code_postal="83000", chauffage_principal="fioul",
                    chauffage_principal_annee=1995, ecs="solaire", ecs_annee=2005))
        await s.commit()
        return user.id


async def _effacer(user_id) -> None:
    async with async_session() as s:
        await s.execute(delete(House).where(House.user_id == user_id))
        await s.execute(delete(User).where(User.id == user_id))
        await s.commit()


@pytest.fixture(scope="module")
def foyer():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0024 non appliquée")
        uid = client.portal.call(_creer_foyer)
        try:
            yield client, {"Authorization": f"Bearer {create_access_token(str(uid))}"}
        finally:
            client.portal.call(lambda: _effacer(uid))
            client.portal.call(engine.dispose)


def _fiche(c, h):
    return c.get("/api/houses/me", headers=h).json()


def test_le_cycle_complet_du_chauffage(foyer):
    c, h = foyer
    avant = _fiche(c, h)
    assert avant["champs_verrouilles"] == []

    # Création : la fiche prend le type et l'année de l'équipement.
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "chauffage", "type": "PAC_air_eau", "annee_pose": 2021, "origine_fiche": "chauffage_principal"})
    assert r.status_code == 201, r.text
    pac = r.json()["id"]
    f = _fiche(c, h)
    assert (f["chauffage_principal"], f["chauffage_principal_annee"]) == ("PAC_air_eau", 2021)
    assert set(f["champs_verrouilles"]) == {"chauffage_principal", "chauffage_principal_annee"}

    # Un second équipement en service sur la même place : refusé.
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "chauffage", "type": "convecteurs", "origine_fiche": "chauffage_principal"})
    assert r.status_code == 409

    # Modification de la date : la fiche suit.
    assert c.patch(f"/api/houses/me/equipements/{pac}", headers=h, json={"date_pose": "2022-04-01"}).status_code == 200
    assert _fiche(c, h)["chauffage_principal_annee"] == 2022

    # La fiche renvoie son bloc entier (`saveBlock`) : mêmes valeurs acceptées…
    bloc = {k: f[k] for k in ("chauffage_principal", "chauffage_appoint", "ecs", "ecs_annee", "clim",
                              "clim_type", "clim_nb_pieces", "regulation")}
    bloc["chauffage_principal_annee"] = 2022
    bloc["regulation"] = "thermostat"
    r = c.patch("/api/houses/me", headers=h, json=bloc)
    assert r.status_code == 200 and r.json()["regulation"] == "thermostat"
    # … mais pas un champ verrouillé qui change.
    r = c.patch("/api/houses/me", headers=h, json={"chauffage_principal_annee": 2010})
    assert r.status_code == 400 and "Mes équipements" in r.json()["detail"]
    # Un champ libre de la même fiche reste modifiable.
    assert c.patch("/api/houses/me", headers=h, json={"ecs_annee": 2006}).status_code == 200

    # Remplacement : l'ancien passe hors service (fiche vidée), le nouveau hérite de l'origine.
    score_avec = _fiche(c, h)["completeness_score"]
    r = c.patch(f"/api/houses/me/equipements/{pac}", headers=h, json={"en_service": False})
    assert r.status_code == 200
    f = _fiche(c, h)
    assert f["chauffage_principal"] is None and f["chauffage_principal_annee"] is None
    assert f["champs_verrouilles"] == []
    assert f["completeness_score"] < score_avec  # recalculé : le chauffage n'est plus renseigné
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "chauffage", "type": "chaudiere_gaz", "annee_pose": 2026, "origine_fiche": "chauffage_principal"})
    gaz = r.json()["id"]
    f = _fiche(c, h)
    assert (f["chauffage_principal"], f["chauffage_principal_annee"]) == ("gaz", 2026)

    # Remettre en service l'ancien, déjà remplacé : refusé.
    assert c.patch(f"/api/houses/me/equipements/{pac}", headers=h, json={"en_service": True}).status_code == 409

    # Suppression d'un équipement en service = hors service sans remplaçant.
    assert c.delete(f"/api/houses/me/equipements/{gaz}", headers=h).status_code == 204
    f = _fiche(c, h)
    assert f["chauffage_principal"] is None and f["champs_verrouilles"] == []
    # Le PAC, seul à nouveau, peut revenir en service : la fiche reprend ses valeurs.
    assert c.patch(f"/api/houses/me/equipements/{pac}", headers=h, json={"en_service": True}).status_code == 200
    assert _fiche(c, h)["chauffage_principal"] == "PAC_air_eau"


def test_eau_chaude_autre_laisse_la_fiche_libre(foyer):
    c, h = foyer
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "ecs", "type": "autre", "annee_pose": 2015, "origine_fiche": "ecs"})
    assert r.status_code == 201
    f = _fiche(c, h)
    assert f["ecs"] == "solaire" and "ecs" not in f["champs_verrouilles"]
    assert c.patch("/api/houses/me", headers=h, json={"ecs": "gaz"}).status_code == 200


def test_la_clim_ecrit_son_libelle_et_garde_le_nombre_de_pieces(foyer):
    c, h = foyer
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "clim", "type": "PAC_air_air", "origine_fiche": "clim"})
    assert r.status_code == 201
    f = _fiche(c, h)
    assert (f["clim"], f["clim_type"]) == (True, "PAC air/air réversible")
    assert c.patch("/api/houses/me", headers=h, json={"clim_nb_pieces": 3}).status_code == 200
    assert c.patch("/api/houses/me", headers=h, json={"clim_type": "Split"}).status_code == 400


def test_une_origine_hors_de_sa_categorie_est_refusee(foyer):
    c, h = foyer
    r = c.post("/api/houses/me/equipements", headers=h, json={
        "categorie": "ventilation", "type": "VMC_simple", "origine_fiche": "ecs"})
    assert r.status_code == 400
