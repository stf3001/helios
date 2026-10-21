"""Carnet, lot 4 : journal, « C'est fait » et bloc « À faire », CONTRE LA VRAIE BASE et la vraie table.

Même outillage que `test_carnet_api.py` (sauté sans Postgres, foyers jetables effacés).
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.db import engine
from app.core.security import create_access_token
from app.main import app
from tests.test_carnet_api import _base_prete, _creer_document, _creer_foyer, _effacer


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent")
        a = client.portal.call(lambda: _creer_foyer(type_logement="maison"))
        b = client.portal.call(lambda: _creer_foyer(type_logement="maison"))
        doc_b = client.portal.call(lambda: _creer_document(b[1]))
        try:
            yield {"c": client, "doc_b": str(doc_b),
                   "a": {"Authorization": f"Bearer {create_access_token(str(a[0]))}"},
                   "b": {"Authorization": f"Bearer {create_access_token(str(b[0]))}"}}
        finally:
            client.portal.call(lambda: _effacer([a[0], b[0]]))
            client.portal.call(engine.dispose)


def _echeance(c, h, tache_id):
    return [e for e in c.get("/api/houses/me/entretien", headers=h).json()["echeances"] if e["tache_id"] == tache_id][0]


def test_sans_equipement_le_bloc_le_dit(ctx):
    r = ctx["c"].get("/api/houses/me/a-faire", headers=ctx["a"]).json()
    assert r["sans_equipement"] is True and r["table_vide"] is False


def test_c_est_fait_decale_l_echeance(ctx):
    c, a = ctx["c"], ctx["a"]
    eq = c.post("/api/houses/me/equipements", headers=a, json={
        "categorie": "chauffage", "type": "chaudiere_gaz", "date_pose": "2018-11-05", "puissance": 24, "unite": "kW"}).json()
    avant = _echeance(c, a, "chaudiere-entretien")
    assert (avant["statut"], avant["echeance"]) == ("en_retard", "2019-12-31")
    bloc = c.get("/api/houses/me/a-faire", headers=a).json()
    assert any(l["kind"] == "tache" and l["tache_id"] == "chaudiere-entretien" for l in bloc["lignes"])

    r = c.post("/api/houses/me/entretien/chaudiere-entretien/fait", headers=a, json={
        "equipement_id": eq["id"], "date": "2026-03-10", "intervenant": "Chauffagiste du coin", "cout_eur": 140})
    assert r.status_code == 201, r.text
    assert r.json()["type"] == "entretien" and r.json()["titre"].startswith("Entretien annuel")
    apres = _echeance(c, a, "chaudiere-entretien")
    assert (apres["provenance"], apres["date_reference"], apres["echeance"]) == ("journal", "2026-03-10", "2027-12-31")
    bloc = c.get("/api/houses/me/a-faire", headers=a).json()
    assert not any(l.get("tache_id") == "chaudiere-entretien" for l in bloc["lignes"])


def test_tache_de_maison_et_controles(ctx):
    c, a = ctx["c"], ctx["a"]
    assert c.post("/api/houses/me/entretien/detecteur-fumee-test/fait", headers=a, json={}).status_code == 201
    assert _echeance(c, a, "detecteur-fumee-test")["provenance"] == "journal"
    # Une tâche d'équipement sans équipement, et l'inverse : refusées.
    assert c.post("/api/houses/me/entretien/chaudiere-entretien/fait", headers=a, json={}).status_code == 400
    assert c.post("/api/houses/me/entretien/inconnue/fait", headers=a, json={}).status_code == 404


def test_une_date_dans_le_futur_est_refusee(ctx):
    c, a = ctx["c"], ctx["a"]
    demain = (date.today() + timedelta(days=1)).isoformat()
    assert c.post("/api/houses/me/entretien/detecteur-fumee-test/fait", headers=a, json={"date": demain}).status_code == 422
    assert c.post("/api/houses/me/journal", headers=a,
                  json={"date": demain, "type": "autre", "titre": "Demain"}).status_code == 422


def test_journal_fusionne_entrees_et_travaux(ctx):
    c, a = ctx["c"], ctx["a"]
    c.post("/api/houses/me/travaux", headers=a, json={"nature": "Isolation des combles", "date_reception": "2025-11-20"})
    c.post("/api/houses/me/journal", headers=a, json={"date": "2026-01-15", "type": "reparation", "titre": "Fuite sous l'évier"})
    lignes = c.get("/api/houses/me/journal", headers=a).json()
    dates = [l["date"] for l in lignes]
    assert dates == sorted(dates, reverse=True)
    assert {l["source"] for l in lignes} == {"journal", "travaux"}
    travaux = [l for l in lignes if l["source"] == "travaux"][0]
    assert travaux["titre"] == "Isolation des combles" and travaux["date"] == "2025-11-20"


def test_un_foyer_ne_touche_pas_le_journal_d_un_autre(ctx):
    c, a, b = ctx["c"], ctx["a"], ctx["b"]
    e = c.post("/api/houses/me/journal", headers=a, json={"date": "2026-02-01", "type": "autre", "titre": "Privé"}).json()
    assert all(l["id"] != e["id"] for l in c.get("/api/houses/me/journal", headers=b).json())
    assert c.patch(f"/api/houses/me/journal/{e['id']}", headers=b, json={"titre": "X"}).status_code == 404
    assert c.delete(f"/api/houses/me/journal/{e['id']}", headers=b).status_code == 404
    r = c.post("/api/houses/me/journal", headers=a,
               json={"date": "2026-02-01", "type": "autre", "titre": "Doc", "document_id": ctx["doc_b"]})
    assert r.status_code == 400
    # Avec son propre document, l'entrée est justifiée.
    r = c.post("/api/houses/me/journal", headers=b,
               json={"date": "2026-02-01", "type": "reparation", "titre": "Facture", "document_id": ctx["doc_b"]})
    assert r.status_code == 201
    assert [l["justifie"] for l in c.get("/api/houses/me/journal", headers=b).json()] == [True]
