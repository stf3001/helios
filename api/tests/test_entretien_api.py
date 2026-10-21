"""Carnet, lot 3 : `GET /houses/me/entretien`, CONTRE LA VRAIE BASE.

Même outillage que `test_carnet_api.py` (sauté sans Postgres). Deux cas : la table livrée,
vide, et la table d'EXEMPLE substituée à la table de production le temps d'un test.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.db import engine
from app.core.security import create_access_token
from app.main import app
from app.services.entretien import charger_table
from tests.test_carnet_api import _base_prete, _creer_foyer, _effacer

EXEMPLE = charger_table(Path(__file__).parent / "fixtures" / "entretien_exemple.json", strict=True)


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent")
        a = client.portal.call(lambda: _creer_foyer(type_logement="maison"))
        try:
            yield client, {"Authorization": f"Bearer {create_access_token(str(a[0]))}"}
        finally:
            client.portal.call(lambda: _effacer([a[0]]))
            client.portal.call(engine.dispose)


def test_vraie_table_maison_sans_equipement(ctx):
    """Une maison sans équipement : le détecteur de fumée, et la question du débroussaillement."""
    c, h = ctx
    r = c.get("/api/houses/me/entretien", headers=h)
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["table_vide"] is False and corps["taches_validees"] == 18
    assert [e["tache_id"] for e in corps["echeances"]] == ["detecteur-fumee-test"]
    assert [(v["tache_id"], v["lien"]) for v in corps["verifications"]] == [
        ("debroussaillement", "https://www.service-public.gouv.fr/particuliers/vosdroits/F33298")]


def test_sans_compte_refuse():
    with TestClient(app) as c:
        assert c.get("/api/houses/me/entretien").status_code == 401


def test_avec_la_table_d_exemple(ctx, monkeypatch):
    c, h = ctx
    monkeypatch.setattr("app.routers.entretien.table_courante", lambda: EXEMPLE)
    c.post("/api/houses/me/equipements", headers=h,
           json={"categorie": "chauffage", "type": "PAC_air_eau", "date_pose": "2020-03-15"})
    c.post("/api/houses/me/equipements", headers=h,
           json={"categorie": "ventilation", "type": "VMC_simple", "en_service": False, "annee_pose": 2010})
    corps = c.get("/api/houses/me/entretien", headers=h).json()
    assert corps["table_vide"] is False and corps["taches_validees"] == 8
    par_tache = {e["tache_id"]: e for e in corps["echeances"]}
    pac = par_tache["exemple-pac-24-mois"]
    assert (pac["echeance"], pac["provenance"], pac["statut"]) == ("2022-03-15", "date_pose", "en_retard")
    assert "exemple-vmc-toute-categorie" not in par_tache   # VMC hors service
    assert "exemple-maison" in par_tache and "exemple-maison-sous-condition" in par_tache  # type_logement=maison
    # zone_old vaut « ne sais pas » par défaut : pas d'obligation, une vérification.
    assert "exemple-maison-zone" not in par_tache
    assert [v["tache_id"] for v in corps["verifications"]] == ["exemple-maison-zone"]
