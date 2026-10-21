"""Carnet de maison, lot 2 : pièces, émetteurs et photos, CONTRE LA VRAIE BASE.

Même principe que `test_carnet_api.py`, dont il reprend l'outillage : sauté entièrement
sans le Postgres de développement (migration 0025), deux foyers jetables effacés en fin
de module. Les fichiers envoyés vont dans un dossier temporaire, jamais dans
`generated/house_docs/`.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house_document import HouseDocument
from app.models.piece import Emetteur
from app.routers import documents
from tests.test_carnet_api import _creer_foyer, _effacer

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


async def _base_prete() -> bool:
    await engine.dispose()  # même raison que dans test_carnet_api.py
    try:
        async with async_session() as s:
            await s.execute(text("SELECT piece_id FROM house_documents LIMIT 1"))
            await s.execute(text("SELECT 1 FROM emetteurs LIMIT 1"))
        return True
    except Exception:
        return False


async def _compter(modele, *conditions) -> int:
    async with async_session() as s:
        return await s.scalar(select(func.count()).select_from(modele).where(*conditions))


async def _document(doc_id):
    async with async_session() as s:
        return await s.get(HouseDocument, doc_id)


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    dossier = tmp_path_factory.mktemp("house_docs")
    ancien, documents.DOCS_DIR = documents.DOCS_DIR, dossier
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            documents.DOCS_DIR = ancien
            pytest.skip("Postgres de développement absent ou migration 0025 non appliquée")
        a = client.portal.call(lambda: _creer_foyer(surface_habitable=110, clim_nb_pieces=2))
        b = client.portal.call(_creer_foyer)
        try:
            yield {
                "c": client, "portal": client.portal, "dossier": dossier,
                "a": {"Authorization": f"Bearer {create_access_token(str(a[0]))}"},
                "b": {"Authorization": f"Bearer {create_access_token(str(b[0]))}"},
            }
        finally:
            client.portal.call(lambda: _effacer([a[0], b[0]]))
            client.portal.call(engine.dispose)
            documents.DOCS_DIR = ancien


DEMARRAGE = {"pieces": [
    {"nom": "Séjour", "type": "sejour", "surface_m2": 30}, {"nom": "Cuisine", "type": "cuisine", "surface_m2": 12},
    {"nom": "Chambre 1", "type": "chambre", "surface_m2": 12}, {"nom": "Chambre 2", "type": "chambre", "surface_m2": 10},
    {"nom": "Salle de bain", "type": "salle_de_bain", "surface_m2": 6}, {"nom": "WC", "type": "wc", "surface_m2": 2},
]}


def _pieces(ctx):
    return ctx["c"].get("/api/houses/me/pieces", headers=ctx["a"]).json()


def test_demarrage_puis_refus_du_second(ctx):
    c, a = ctx["c"], ctx["a"]
    r = c.post("/api/houses/me/pieces/demarrage", headers=a, json=DEMARRAGE)
    assert r.status_code == 201 and r.json() == {"crees": 6}
    assert [p["nom"] for p in _pieces(ctx)][:2] == ["Séjour", "Cuisine"]
    assert c.post("/api/houses/me/pieces/demarrage", headers=a, json=DEMARRAGE).status_code == 409


def test_resume_signale_les_ecarts_sans_toucher_la_fiche(ctx):
    c, a = ctx["c"], ctx["a"]
    sejour = _pieces(ctx)[0]
    c.post(f"/api/houses/me/pieces/{sejour['id']}/emetteurs", headers=a,
           json={"type": "unite_interieure_clim", "puissance_w": 2500})
    r = c.get("/api/houses/me/pieces/resume", headers=a).json()
    assert r["surface_pieces_m2"]["valeur"] == 72
    assert r["ecart_surface"]["fiche_m2"] == 110  # 72 contre 110 : -35 %
    assert r["ecart_clim"] == {**r["ecart_clim"], "pieces": 1, "fiche": 2}
    assert len(r["chauffees_sans_emetteur"]["valeur"]) == 5
    fiche = c.get("/api/houses/me", headers=a).json()
    assert fiche["surface_habitable"] == 110 and fiche["clim_nb_pieces"] == 2


def test_robinet_thermostatique_reserve_au_radiateur_a_eau(ctx):
    c, a = ctx["c"], ctx["a"]
    cuisine = _pieces(ctx)[1]
    e = c.post(f"/api/houses/me/pieces/{cuisine['id']}/emetteurs", headers=a,
               json={"type": "convecteur", "robinet_thermostatique": True}).json()
    assert e["robinet_thermostatique"] is None
    e = c.patch(f"/api/houses/me/pieces/{cuisine['id']}/emetteurs/{e['id']}", headers=a,
                json={"type": "radiateur_eau", "nombre": 2, "robinet_thermostatique": True}).json()
    assert e["robinet_thermostatique"] is True and e["nombre"] == 2


def test_photo_hors_limite_remplacee_et_gardee_apres_suppression(ctx):
    c, a = ctx["c"], ctx["a"]
    for i in range(6):
        r = c.post("/api/houses/me/documents", headers=a, data={"type": "facture"},
                   files={"file": (f"f{i}.pdf", b"%PDF-1.4", "application/pdf")})
        assert r.status_code == 201, r.text
    assert c.post("/api/houses/me/documents", headers=a, data={"type": "facture"},
                  files={"file": ("f7.pdf", b"%PDF", "application/pdf")}).status_code == 400

    chambre = _pieces(ctx)[2]
    p1 = c.post("/api/houses/me/documents", headers=a, data={"type": "devis", "piece_id": chambre["id"]},
                files={"file": ("chambre.png", PNG, "image/png")})
    assert p1.status_code == 201, p1.text
    assert p1.json()["type"] == "photo" and p1.json()["piece_id"] == chambre["id"]
    premier_fichier = list(ctx["dossier"].glob("*.png"))
    assert len(premier_fichier) == 1

    p2 = c.post("/api/houses/me/documents", headers=a, data={"piece_id": chambre["id"]},
                files={"file": ("chambre-bis.png", PNG, "image/png")})
    assert p2.status_code == 201
    assert not premier_fichier[0].exists()  # l'ancien fichier a quitté le disque
    assert ctx["portal"].call(lambda: _compter(HouseDocument, HouseDocument.piece_id == chambre["id"])) == 1
    assert [p for p in _pieces(ctx) if p["id"] == chambre["id"]][0]["photo"]["filename"] == "chambre-bis.png"

    assert c.delete(f"/api/houses/me/pieces/{chambre['id']}", headers=a).status_code == 204
    doc = ctx["portal"].call(lambda: _document(p2.json()["id"]))
    assert doc is not None and doc.piece_id is None and Path(doc.path).exists()


def test_les_emetteurs_partent_avec_leur_piece(ctx):
    c, a = ctx["c"], ctx["a"]
    sdb = [p for p in _pieces(ctx) if p["type"] == "salle_de_bain"][0]
    c.post(f"/api/houses/me/pieces/{sdb['id']}/emetteurs", headers=a, json={"type": "seche_serviettes"})
    assert ctx["portal"].call(lambda: _compter(Emetteur, Emetteur.piece_id == sdb["id"])) == 1
    assert c.delete(f"/api/houses/me/pieces/{sdb['id']}", headers=a).status_code == 204
    assert ctx["portal"].call(lambda: _compter(Emetteur, Emetteur.piece_id == sdb["id"])) == 0


def test_un_foyer_ne_touche_pas_les_pieces_d_un_autre(ctx):
    c, a, b = ctx["c"], ctx["a"], ctx["b"]
    piece = _pieces(ctx)[0]
    assert c.get("/api/houses/me/pieces", headers=b).json() == []
    assert c.patch(f"/api/houses/me/pieces/{piece['id']}", headers=b, json={"nom": "X"}).status_code == 404
    assert c.delete(f"/api/houses/me/pieces/{piece['id']}", headers=b).status_code == 404
    assert c.post(f"/api/houses/me/pieces/{piece['id']}/emetteurs", headers=b,
                  json={"type": "convecteur"}).status_code == 404
    assert c.post("/api/houses/me/documents", headers=b, data={"piece_id": piece["id"]},
                  files={"file": ("x.png", PNG, "image/png")}).status_code == 404
    # Relier son émetteur à l'équipement d'un autre foyer est refusé.
    eq = c.post("/api/houses/me/equipements", headers=a, json={"categorie": "chauffage", "type": "chaudiere_gaz"}).json()
    piece_b = c.post("/api/houses/me/pieces", headers=b, json={"nom": "Séjour", "type": "sejour"}).json()
    r = c.post(f"/api/houses/me/pieces/{piece_b['id']}/emetteurs", headers=b,
               json={"type": "radiateur_eau", "equipement_id": eq["id"]})
    assert r.status_code == 400
    r = c.post(f"/api/houses/me/pieces/{piece['id']}/emetteurs", headers=a,
               json={"type": "radiateur_eau", "equipement_id": eq["id"]})
    assert r.status_code == 201
