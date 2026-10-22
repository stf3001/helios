"""Carnet, lot 8 : les quatre foyers par l'API, CONTRE LA VRAIE BASE (sauté sans elle).

Même dispositif que `test_carnet_api.py` : foyers jetables, effacés en fin de module.
"""

import io
import uuid
from pathlib import Path

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
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT chauffage_collectif, avant_achat FROM houses LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer(**fiche) -> uuid.UUID:
    async with async_session() as s:
        user = User(email=f"lot8-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        s.add(House(user_id=user.id, code_postal="83000", **fiche))
        await s.commit()
        return user.id


async def _effacer(uids) -> None:
    async with async_session() as s:
        for uid in uids:
            house_id = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
            if house_id:
                for chemin in await s.scalars(text("SELECT path FROM house_documents WHERE house_id = :h"),
                                              {"h": house_id}):
                    Path(chemin).unlink(missing_ok=True)  # le dépôt de l'acheteur écrit un vrai fichier
                await s.execute(delete(HouseDocument).where(HouseDocument.house_id == house_id))
                await s.execute(delete(House).where(House.id == house_id))
            await s.execute(delete(User).where(User.id == uid))
        await s.commit()


@pytest.fixture(scope="module")
def foyers():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0031 non appliquée")
        uids = {
            "locataire": client.portal.call(lambda: _creer_foyer(statut="locataire", type_logement="maison", zone_old="oui")),
            "appartement": client.portal.call(lambda: _creer_foyer(statut="proprietaire", type_logement="appartement")),
            "acheteur": client.portal.call(lambda: _creer_foyer(statut="en_achat", type_logement="maison")),
        }
        try:
            yield client, {k: {"Authorization": f"Bearer {create_access_token(str(v))}"} for k, v in uids.items()}
        finally:
            client.portal.call(lambda: _effacer(uids.values()))
            client.portal.call(engine.dispose)


def _equipement(c, h, **corps):
    r = c.post("/api/houses/me/equipements", headers=h, json=corps)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_locataire(foyers):
    c, h = foyers
    h = h["locataire"]
    _equipement(c, h, categorie="eau", type="fosse_septique", annee_pose=2005)
    _equipement(c, h, categorie="ecs", type="ballon_elec", annee_pose=2010)
    c.post("/api/houses/me/travaux", headers=h, json={"nature": "Toiture", "date_reception": "2025-03-15"})
    assert c.get("/api/houses/me", headers=h).json()["parcours"]["profil"] == "locataire"

    entretien = c.get("/api/houses/me/entretien", headers=h).json()["echeances"]
    spanc = [e for e in entretien if e["tache_id"] == "spanc-controle"][0]
    assert spanc["pour_moi"] is False and "propriétaire" in spanc["mention"]
    bloc = c.get("/api/houses/me/a-faire", headers=h).json()
    ids = {l.get("tache_id") for l in bloc["lignes"]}
    assert "spanc-controle" not in ids and "debroussaillement" not in ids and "ballon-groupe-securite" in ids
    assert not [l for l in bloc["lignes"] if l["kind"] == "garantie" and l.get("provenance") == "travaux"]

    texte = c.get("/api/houses/me/note-proprietaire", headers=h).json()["texte"]
    assert "sauf clause contraire" in texte and "Fosse septique" in texte


def test_la_note_est_reservee_aux_locataires(foyers):
    c, h = foyers
    assert c.get("/api/houses/me/note-proprietaire", headers=h["appartement"]).status_code == 400


def test_appartement_en_chauffage_collectif(foyers):
    c, h = foyers
    h = h["appartement"]
    _equipement(c, h, categorie="chauffage", type="chaudiere_gaz", annee_pose=2015)
    _equipement(c, h, categorie="eau", type="fosse_septique", annee_pose=2015)
    ids = {e["tache_id"] for e in c.get("/api/houses/me/entretien", headers=h).json()["echeances"]}
    assert "spanc-controle" not in ids and "debroussaillement" not in ids
    assert c.patch("/api/houses/me", headers=h, json={"chauffage_collectif": "oui"}).status_code == 200
    chaudiere = [e for e in c.get("/api/houses/me/entretien", headers=h).json()["echeances"]
                 if e["tache_id"] == "chaudiere-entretien"][0]
    assert chaudiere["pour_moi"] is False and chaudiere["mention"] == "Assuré par la copropriété."
    assert "chaudiere-entretien" not in {l.get("tache_id") for l in c.get("/api/houses/me/a-faire", headers=h).json()["lignes"]}
    # Un « non renseigné » renvoyé par la fiche redevient « je ne sais pas » (colonne NOT NULL).
    assert c.patch("/api/houses/me", headers=h, json={"chauffage_collectif": None}).json()["chauffage_collectif"] == "ne_sais_pas"


def test_acheteur_coche_joint_puis_devient_proprietaire(foyers):
    c, h = foyers
    h = h["acheteur"]
    assert c.get("/api/houses/me/a-faire", headers=h).json()["parcours"]["avant_d_acheter"] is True
    lignes = c.get("/api/houses/me/avant-achat", headers=h).json()["lignes"]
    assert len(lignes) == 7 and not any(l["coche"] for l in lignes)

    doc = c.post("/api/houses/me/documents", headers=h, data={"type": "dpe"},
                 files={"file": ("dpe.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")})
    assert doc.status_code == 201, doc.text
    r = c.patch("/api/houses/me/avant-achat/dpe", headers=h, json={"coche": True, "document_id": doc.json()["id"]})
    assert r.status_code == 200 and r.json()["lignes"][0]["coche"] is True
    assert c.patch("/api/houses/me/avant-achat/inconnu", headers=h, json={"coche": True}).status_code == 404
    assert c.patch("/api/houses/me/avant-achat/cil", headers=h,
                   json={"document_id": str(uuid.uuid4())}).status_code == 400

    assert c.patch("/api/houses/me", headers=h, json={"statut": "proprietaire"}).status_code == 200
    journal = c.get("/api/houses/me/journal", headers=h).json()
    archive = [e for e in journal if e["titre"] == "Avant d'acheter : documents demandés au vendeur"]
    assert len(archive) == 1 and "Reçu — Le diagnostic de performance énergétique (DPE) (document joint : dpe.pdf)" in archive[0]["note"]
    assert c.get("/api/houses/me", headers=h).json()["parcours"]["avant_d_acheter"] is False
    assert not any(l["coche"] for l in c.get("/api/houses/me/avant-achat", headers=h).json()["lignes"])
