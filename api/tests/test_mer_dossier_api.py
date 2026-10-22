"""Mises en relation, lot 2 : dossier transmis, copies de documents, retrait, vue partenaire — contre la base de dev."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token, create_partner_token
from app.main import app
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.partner import Partner
from app.models.projet import Projet
from app.models.user import User
from app.routers.documents import DOCS_DIR
from app.routers.leads import LEAD_DOCS_DIR
from tests.outils_mer import assurer_charte, mettre_en_regle, retirer_charte

PREFIXE = "MER2-TEST "
PDL = "98765432109876"


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT dossier, creneaux FROM leads LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer() -> dict:
    async with async_session() as s:
        p = Partner(raison_sociale=PREFIXE + "Isol", statut="actif", zones=["83"], metiers=["isolation"], rge=True,
                    charte_signee_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
        u = User(email=f"mer2-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x", prenom="Camille")
        charte = await assurer_charte(s)
        s.add_all([p, u])
        await s.flush()
        mettre_en_regle(s, p, charte[0])
        h = House(user_id=u.id, code_postal="83000", type_logement="maison", statut="proprietaire",
                  surface_habitable=110, horizon="<6mois", budget_envisage="15-30k", completeness_score=75.0,
                  pdl=PDL, travaux_deja_faits="Toiture par Martin Couvreur")
        s.add(h)
        await s.flush()
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        fichier = DOCS_DIR / f"{uuid.uuid4()}.pdf"
        fichier.write_bytes(b"%PDF-1.4 devis de test")
        d = HouseDocument(house_id=h.id, type="devis", filename="devis-combles.pdf", path=str(fichier), size=22)
        pr = Projet(house_id=h.id, modele_id="isolation_combles", titre="Isoler les combles", etape="devis",
                    note="Note privée du foyer")
        s.add_all([d, pr])
        await s.commit()
        return {"charte": charte, "partner": p.id, "user": u.id, "house": h.id, "doc": d.id, "fichier": fichier, "projet": pr.id}


async def _effacer(ids) -> None:
    async with async_session() as s:
        await s.execute(text("DELETE FROM leads WHERE house_id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM projets WHERE house_id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM house_documents WHERE house_id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM partners WHERE raison_sociale LIKE :p"), {"p": PREFIXE + "%"})
        await retirer_charte(s, *ids["charte"])
        await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids["user"]})
        await s.commit()
    ids["fichier"].unlink(missing_ok=True)


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0037 non appliquée")
        ids = client.portal.call(_creer)
        try:
            yield client, ids, {"Authorization": f"Bearer {create_access_token(str(ids['user']))}"}, \
                {"Authorization": f"Bearer {create_partner_token(str(ids['partner']))}"}
        finally:
            client.portal.call(lambda: _effacer(ids))
            client.portal.call(engine.dispose)


def _demande(ids, **kw):
    corps = {"metier": "isolation", "message": "Devis pour les combles, svp",
             "partage": {"fiche": True, "projet_id": str(ids["projet"]), "document_ids": [str(ids["doc"])]},
             "contact": {"nom": "Camille D.", "telephone": "06 11 22 33 44", "email": "camille@example.com"},
             "creneaux": [{"jour": "samedi", "plage": "matin"}, {"jour": "mardi", "plage": "soir"}]}
    corps.update(kw)
    return corps


def test_partageable_ne_coche_rien_et_preremplit_le_contact(ctx):
    c, ids, h, _ = ctx
    r = c.get("/api/leads/partageable", headers=h).json()
    assert r["contact"]["nom"] == "Camille" and r["documents_max"] == 5
    assert [p["titre"] for p in r["projets"]] == ["Isoler les combles"]
    assert r["etudes"] == {"audit": None, "simulateur": None}
    assert r["documents"][0]["filename"] == "devis-combles.pdf"


def test_sans_creneau_ni_coordonnees_refuse(ctx):
    c, ids, h, _ = ctx
    base = {"partner_id": str(ids["partner"]), "type": "travaux", "consent": True}
    r = c.post("/api/leads", headers=h, json={**base, **_demande(ids, creneaux=[])})
    assert r.status_code == 400 and "créneau" in r.json()["detail"]
    sans_contact = _demande(ids)
    sans_contact.pop("contact")
    assert c.post("/api/leads", headers=h, json={**base, **sans_contact}).status_code == 400
    assert c.post("/api/leads/apercu", headers=h, json=_demande(ids, partage={"etude": "audit"})).status_code == 400
    six = _demande(ids, partage={"document_ids": [str(uuid.uuid4()) for _ in range(6)]})
    assert c.post("/api/leads/apercu", headers=h, json=six).status_code == 400


def test_parcours_complet_apercu_creation_vue_partenaire_copie_retrait(ctx):
    c, ids, h, hp = ctx
    apercu = c.post("/api/leads/apercu", headers=h, json=_demande(ids)).json()
    assert apercu["creneaux"] == [{"jour": "mardi", "plage": "soir"}, {"jour": "samedi", "plage": "matin"}]
    assert apercu["score"] == 20 + 20 + 15 + 10 + 15  # tout sauf l'étude récente, non partagée
    for interdit in (PDL, "Martin Couvreur", "Note privée", str(ids["fichier"])):
        assert interdit not in repr(apercu)

    r = c.post("/api/leads", headers=h, json={"partner_id": str(ids["partner"]), "type": "travaux",
                                              "consent": True, **_demande(ids)})
    assert r.status_code == 201, r.text
    lead_id = r.json()["id"]

    # Ce que voit le partenaire est exactement l'aperçu.
    vue = c.get(f"/api/partner/leads/{lead_id}", headers=hp).json()
    assert vue["dossier"] == apercu["dossier"] and vue["score_detail"] == apercu["score_detail"]
    assert vue["creneaux"] == apercu["creneaux"] and vue["contact"]["telephone"] == "06 11 22 33 44"
    assert "L. 223-1" in vue["rappel_legal"] and vue["prix_ht"] == 60
    assert c.get("/api/partner/leads", headers=hp).json()[0]["score"] == 80

    # La copie survit à la suppression du document de la maison.
    assert c.delete(f"/api/houses/me/documents/{ids['doc']}", headers=h).status_code == 204
    assert not ids["fichier"].exists()
    doc = c.get(f"/api/partner/leads/{lead_id}/documents/{ids['doc']}", headers=hp)
    assert doc.status_code == 200 and doc.content == b"%PDF-1.4 devis de test"

    # Retrait : copies supprimées, dossier, coordonnées, message et créneaux vidés ; prix gardé.
    assert c.post(f"/api/leads/{lead_id}/withdraw", headers=h).status_code == 200
    assert not (LEAD_DOCS_DIR / lead_id).exists()
    vue = c.get(f"/api/partner/leads/{lead_id}", headers=hp).json()
    assert vue["dossier"] is None and vue["score_detail"] == [] and vue["creneaux"] == []
    assert vue["contact"] == {"nom": None, "telephone": None, "email": None} and vue["message"] is None
    assert vue["statut"] == "perdu" and vue["prix_ht"] == 60
    assert c.get(f"/api/partner/leads/{lead_id}/documents/{ids['doc']}", headers=hp).status_code == 404


def test_un_autre_partenaire_ne_lit_pas_le_dossier(ctx):
    c, _, _, _ = ctx
    autre = {"Authorization": f"Bearer {create_partner_token(str(uuid.uuid4()))}"}
    assert c.get(f"/api/partner/leads/{uuid.uuid4()}", headers=autre).status_code in (401, 404)
