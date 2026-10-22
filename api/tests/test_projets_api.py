"""Carnet, lot 9 : les projets par l'API, CONTRE LA VRAIE BASE (sauté sans elle).

Même dispositif que `test_carnet_api.py` : foyers jetables, effacés en fin de module.
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.audit import Audit
from app.models.equipement import Equipement
from app.models.house import House
from app.models.simulateur import SimulateurStudy
from app.models.user import User
from app.routers import projets as routeur

PRIORITE_PAC = {"action": "pac_air_eau", "cout_eur": {"bas": 14000, "haut": 19000},
                "economie_annuelle_eur": {"bas": 900, "haut": 1300, "central": 1100},
                "statuts": {"cout_eur": "suppose", "economie_annuelle_eur": "calcule"}}
INVEST = {"panneaux_eur": 10521, "carport_eur": 0, "batterie_eur": 0, "inertie_eur": 0, "eolien_eur": 0}


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM projets LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer(statut: str) -> uuid.UUID:
    async with async_session() as s:
        user = User(email=f"lot9-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        house = House(user_id=user.id, code_postal="83000", statut=statut, type_logement="maison",
                      chauffage_principal="fioul", chauffage_principal_annee=1998)
        s.add(house)
        await s.flush()
        s.add(Equipement(house_id=house.id, categorie="chauffage", type="chaudiere_fioul", annee_pose=1998,
                         origine_fiche="chauffage_principal"))
        s.add(Audit(house_id=house.id, json_result={"priorites": [PRIORITE_PAC]}))
        s.add(SimulateurStudy(house_id=house.id, configuration={}, version_moteur="simu-2",
                              resultat={"investissement": INVEST, "indicateurs": {"economie_1re_annee_eur": 640}}))
        await s.commit()
        return user.id


async def _effacer(uids) -> None:
    async with async_session() as s:
        for uid in uids:
            h = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
            if h:
                for table in ("audits", "simulateur_studies", "journal_maison", "projets", "equipements", "travaux"):
                    await s.execute(text(f"DELETE FROM {table} WHERE house_id = :h"), {"h": h})
                await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": h})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        await s.commit()


async def _compter(uid, table) -> int:
    async with async_session() as s:
        return await s.scalar(text(f"SELECT count(*) FROM {table} t JOIN houses h ON h.id = t.house_id "
                                   "WHERE h.user_id = :u"), {"u": uid})


@pytest.fixture(scope="module")
def foyers():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0032 non appliquée")
        uids = {"proprio": client.portal.call(lambda: _creer_foyer("proprietaire")),
                "locataire": client.portal.call(lambda: _creer_foyer("locataire"))}
        try:
            yield client, uids, {k: {"Authorization": f"Bearer {create_access_token(str(v))}"} for k, v in uids.items()}
        finally:
            client.portal.call(lambda: _effacer(uids.values()))
            client.portal.call(engine.dispose)


def test_modeles_et_calculs_existants(foyers):
    c, _, h = foyers
    r = c.get("/api/houses/me/projets/modeles", headers=h["proprio"]).json()
    par_id = {m["id"]: m for m in r["modeles"]}
    assert "sortie-gaz-pac-air-eau" not in par_id
    assert par_id["jardin-hiver"]["outil_lien"] is None and par_id["jardin-hiver"]["calcul"] is None
    assert par_id["sortie-fioul-pac-air-eau"]["calcul"]["type"] == "audit"
    assert par_id["panneaux-solaires"]["calcul"]["type"] == "simulateur"
    assert par_id["batterie"]["calcul"] is None and par_id["batterie"]["outil_lien"] == "/simulateur-solaire"


def test_de_l_idee_a_la_reception(foyers):
    c, _, h = foyers
    h = h["proprio"]
    p = c.post("/api/houses/me/projets", headers=h, json={"modele_id": "sortie-fioul-pac-air-eau"}).json()
    assert p["etape"] == "idee" and p["budget_bas_eur"] is None

    # Lier l'étude : les valeurs du pré-audit, telles quelles, datées.
    r = c.post(f"/api/houses/me/projets/{p['id']}/lier-etude", headers=h).json()
    assert (r["budget_bas_eur"], r["budget_haut_eur"], r["economie_annuelle_eur"]) == (14000, 19000, 1100)
    assert (r["budget_source"], r["budget_statut"], r["economie_statut"]) == ("audit", "suppose", "calcule")
    assert r["budget_date"] == date.today().isoformat() and r["etude_ref"]["type"] == "audit"

    # Un devis reçu : montant déclaré ; l'économie de l'étude reste.
    r = c.patch(f"/api/houses/me/projets/{p['id']}", headers=h, json={"etape": "devis", "devis_montant_eur": 16500}).json()
    assert (r["budget_bas_eur"], r["budget_source"], r["budget_statut"]) == (16500, "devis", "declare")
    assert r["economie_annuelle_eur"] == 1100 and r["etape"] == "devis"
    assert c.patch(f"/api/houses/me/projets/{p['id']}", headers=h, json={"etape": "termine"}).status_code == 400

    # Les travaux sont terminés : chantier, garanties, équipement coché, journal.
    demain = (date.today() + timedelta(days=1)).isoformat()
    assert c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h,
                  json={"date_reception": demain}).status_code == 422
    hier = date.today() - timedelta(days=1)
    r = c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h, json={
        "date_reception": hier.isoformat(), "entreprise": "Entreprise du foyer", "montant_ttc": 16500,
        "equipements": [0]})
    assert r.status_code == 200, r.text
    assert r.json()["etape"] == "termine" and r.json()["travaux_id"]

    chantier = [t for t in c.get("/api/houses/me/travaux", headers=h).json() if t["id"] == r.json()["travaux_id"]][0]
    assert chantier["nature"] == "Sortir du fioul : PAC air/eau" and len(chantier["garanties"]) == 3
    eqs = c.get("/api/houses/me/equipements", headers=h).json()
    pac = [e for e in eqs if e["type"] == "PAC_air_eau"][0]
    assert pac["en_service"] and pac["travaux_id"] == chantier["id"] and pac["date_pose"] == hier.isoformat()
    assert not [e for e in eqs if e["type"] == "chaudiere_fioul"][0]["en_service"]  # remplacée
    fiche = c.get("/api/houses/me", headers=h).json()
    assert (fiche["chauffage_principal"], fiche["chauffage_principal_annee"]) == ("PAC_air_eau", hier.year)
    journal = c.get("/api/houses/me/journal", headers=h).json()
    assert any(e["type"] == "amelioration" and e["titre"] == "Sortir du fioul : PAC air/eau" for e in journal)

    # Clos : il ne bouge plus, sauf sa note.
    assert c.patch(f"/api/houses/me/projets/{p['id']}", headers=h, json={"etape": "idee"}).status_code == 409
    assert c.patch(f"/api/houses/me/projets/{p['id']}", headers=h, json={"note": "RAS"}).status_code == 200


def test_un_echec_en_cours_de_route_annule_tout(foyers, monkeypatch):
    c, uids, h = foyers
    h = h["proprio"]
    p = c.post("/api/houses/me/projets", headers=h, json={"modele_id": "panneaux-solaires"}).json()
    tables = ("travaux", "equipements", "journal_maison")
    avant = {t: c.portal.call(_compter, uids["proprio"], t) for t in tables}

    async def panne(*_):
        raise RuntimeError("panne simulée")
    monkeypatch.setattr(routeur, "_ecrire_journal", panne)
    with pytest.raises(RuntimeError):
        c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h,
               json={"date_reception": date.today().isoformat(), "equipements": [0, 1]})
    assert {t: c.portal.call(_compter, uids["proprio"], t) for t in tables} == avant
    assert c.get(f"/api/houses/me/projets/{p['id']}", headers=h).json()["etape"] == "idee"


def test_lier_sans_calcul_renvoie_vers_l_outil(foyers):
    c, _, h = foyers
    p = c.post("/api/houses/me/projets", headers=h["proprio"], json={"modele_id": "batterie"}).json()
    assert c.post(f"/api/houses/me/projets/{p['id']}/lier-etude", headers=h["proprio"]).status_code == 404
    detail = c.get(f"/api/houses/me/projets/{p['id']}", headers=h["proprio"]).json()
    assert [f["source"] for f in detail["fiches"]] == ["stockage_contrats", "financement_projet",
                                                       "choisir_installateur", "garanties_travaux"]
    assert all(f["questions"] for f in detail["fiches"])


def test_sans_calculateur_lier_etude_est_refuse(foyers):
    c, _, h = foyers
    p = c.post("/api/houses/me/projets", headers=h["proprio"], json={"modele_id": "jardin-hiver"}).json()
    r = c.post(f"/api/houses/me/projets/{p['id']}/lier-etude", headers=h["proprio"])
    assert r.status_code == 409 and "Pas de calculateur" in r.json()["detail"]
    detail = c.get(f"/api/houses/me/projets/{p['id']}", headers=h["proprio"]).json()
    assert detail["fiches"][0]["source"] == "jardin_hiver"


def test_locataire(foyers):
    c, _, h = foyers
    ids = [m["id"] for m in c.get("/api/houses/me/projets/modeles", headers=h["locataire"]).json()["modeles"]]
    assert ids == ["machine-eau-air", "regulation-chauffage"]
    assert c.post("/api/houses/me/projets", headers=h["locataire"],
                  json={"modele_id": "panneaux-solaires"}).status_code == 400
    for _ in range(20):
        assert c.post("/api/houses/me/projets", headers=h["locataire"],
                      json={"modele_id": "machine-eau-air"}).status_code == 201
    assert c.post("/api/houses/me/projets", headers=h["locataire"],
                  json={"modele_id": "machine-eau-air"}).status_code == 400
