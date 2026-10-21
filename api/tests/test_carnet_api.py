"""Carnet de maison, lot 1 : l'API de bout en bout, CONTRE LA VRAIE BASE.

Le reste de la suite tourne sans base ; ce module a besoin du Postgres de développement
(migration 0024 appliquée) et se SAUTE ENTIÈREMENT s'il ne le trouve pas — un clone neuf
reste vert. Deux foyers jetables sont créés puis effacés (la cascade emporte le carnet).

Ce qui est vérifié : un foyer ne lit, ne modifie ni ne supprime l'équipement ou le chantier
d'un autre (404, comme un identifiant inexistant), ne rattache pas le document d'un autre
(400), et le parcours suggestion → équipement fait disparaître la suggestion.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.user import User


async def _base_prete() -> bool:
    # Chaque TestClient tourne sur SA boucle d'événements : des connexions laissées dans le
    # pool par un module précédent y sont inutilisables, et la sonde échouerait — le module
    # se sauterait alors en silence alors que la base est là. On repart d'un pool vide.
    await engine.dispose()
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM equipements LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer(**fiche) -> tuple[uuid.UUID, uuid.UUID]:
    async with async_session() as s:
        user = User(email=f"carnet-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        house = House(user_id=user.id, code_postal="83000", **fiche)
        s.add(house)
        await s.commit()
        return user.id, house.id


async def _creer_document(house_id) -> uuid.UUID:
    async with async_session() as s:
        doc = HouseDocument(house_id=house_id, type="facture", filename="f.pdf", path="/nulle/part.pdf")
        s.add(doc)
        await s.commit()
        return doc.id


async def _effacer(user_ids) -> None:
    async with async_session() as s:
        for uid in user_ids:
            house_id = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
            if house_id:
                await s.execute(delete(HouseDocument).where(HouseDocument.house_id == house_id))
                await s.execute(delete(House).where(House.id == house_id))
            await s.execute(delete(User).where(User.id == uid))
        await s.commit()


@pytest.fixture(scope="module")
def foyers():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0024 non appliquée")
        a = client.portal.call(lambda: _creer_foyer(
            chauffage_principal="PAC_air_eau", chauffage_principal_annee=2016,
            ecs="ballon_elec", ecs_annee=2010))
        b = client.portal.call(_creer_foyer)
        doc_b = client.portal.call(lambda: _creer_document(b[1]))
        try:
            yield {
                "client": client,
                "a": {"Authorization": f"Bearer {create_access_token(str(a[0]))}"},
                "b": {"Authorization": f"Bearer {create_access_token(str(b[0]))}"},
                "doc_b": str(doc_b),
            }
        finally:
            client.portal.call(lambda: _effacer([a[0], b[0]]))
            client.portal.call(engine.dispose)


def test_suggestion_puis_equipement_puis_disparition(foyers):
    c, a = foyers["client"], foyers["a"]
    sugg = c.get("/api/houses/me/equipements/suggestions", headers=a).json()
    assert [s["origine_fiche"] for s in sugg] == ["chauffage_principal", "ecs"]
    pac = sugg[0]
    r = c.post("/api/houses/me/equipements", headers=a, json={
        "categorie": pac["categorie"], "type": pac["type"], "annee_pose": pac["annee_pose"],
        "origine_fiche": pac["origine_fiche"], "marque": "Atlantic", "numero_serie": "SN-123"})
    assert r.status_code == 201, r.text
    assert r.json()["age_statut"] == "suppose" and r.json()["age_ans"] >= 10
    sugg = c.get("/api/houses/me/equipements/suggestions", headers=a).json()
    assert [s["origine_fiche"] for s in sugg] == ["ecs"]


def test_type_hors_de_sa_categorie_refuse(foyers):
    c, a = foyers["client"], foyers["a"]
    r = c.post("/api/houses/me/equipements", headers=a, json={"categorie": "ecs", "type": "PAC_air_eau"})
    assert r.status_code == 422


def test_un_foyer_ne_touche_pas_l_equipement_d_un_autre(foyers):
    c, a, b = foyers["client"], foyers["a"], foyers["b"]
    eq = c.post("/api/houses/me/equipements", headers=a,
                json={"categorie": "eau", "type": "adoucisseur"}).json()
    assert all(e["id"] != eq["id"] for e in c.get("/api/houses/me/equipements", headers=b).json())
    assert c.patch(f"/api/houses/me/equipements/{eq['id']}", headers=b, json={"marque": "X"}).status_code == 404
    assert c.delete(f"/api/houses/me/equipements/{eq['id']}", headers=b).status_code == 404
    # Mise hors service puis suppression par son propriétaire.
    r = c.patch(f"/api/houses/me/equipements/{eq['id']}", headers=a, json={"en_service": False})
    assert r.status_code == 200 and r.json()["en_service"] is False
    assert c.delete(f"/api/houses/me/equipements/{eq['id']}", headers=a).status_code == 204


def test_un_foyer_ne_touche_pas_le_chantier_d_un_autre(foyers):
    c, a, b = foyers["client"], foyers["a"], foyers["b"]
    t = c.post("/api/houses/me/travaux", headers=a,
               json={"nature": "Isolation des combles", "date_reception": "2025-03-15"}).json()
    assert [g["fin"] for g in t["garanties"]] == ["2026-03-15", "2027-03-15", "2035-03-15"]
    assert c.get("/api/houses/me/travaux", headers=b).json() == []
    assert c.patch(f"/api/houses/me/travaux/{t['id']}", headers=b, json={"nature": "X"}).status_code == 404
    assert c.delete(f"/api/houses/me/travaux/{t['id']}", headers=b).status_code == 404
    # Rattacher son équipement au chantier d'un autre est refusé.
    r = c.post("/api/houses/me/equipements", headers=b,
               json={"categorie": "autre", "type": "autre", "travaux_id": t["id"]})
    assert r.status_code == 400
    garanties = c.get("/api/houses/me/garanties", headers=a).json()
    assert {g["code"] for g in garanties if g["provenance"] == "travaux"} == {
        "parfait_achevement", "bon_fonctionnement", "decennale"}
    assert c.get("/api/houses/me/garanties", headers=b).json() == []


def test_le_document_d_un_autre_foyer_est_refuse(foyers):
    c, a, b = foyers["client"], foyers["a"], foyers["b"]
    r = c.post("/api/houses/me/travaux", headers=a, json={"nature": "Toiture", "facture_document_id": foyers["doc_b"]})
    assert r.status_code == 400
    r = c.post("/api/houses/me/travaux", headers=b, json={"nature": "Toiture", "facture_document_id": foyers["doc_b"]})
    assert r.status_code == 201
