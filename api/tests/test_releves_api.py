"""Mises en relation, lot 4 : relevés, clôture et PDF — contre la base de dev.

Les tests travaillent sur JANVIER 2025, un mois sans rien d'autre en base : la clôture est
globale à un mois, elle ne doit toucher ni les données de démonstration ni le mois en cours.
Tout est effacé en fin de module (lignes, clôture, PDF).
"""
import io
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import select, text

from app.core.config import settings
from app.core.db import async_session, engine
from app.core.security import create_partner_token
from app.main import app
from app.models.house import House
from app.models.partner import Contestation, Lead, Partner, Releve
from app.models.user import User
from app.services import releves_lecture
from app.services.creneaux import a_paris
from app.services.pdf_releve import MENTION, releve_pdf

MOIS = "2025-01"
PREFIXE = "REL-TEST "
ADMIN = {"X-Admin-Token": "secret-de-test-releves"}
NOM_FOYER = "Camille Foyer-Secret"


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM releves_clotures LIMIT 1"))
            return await s.scalar(text("SELECT count(*) FROM releves_clotures WHERE mois = :m"), {"m": MOIS}) == 0
    except Exception:
        return False


async def _creer() -> dict:
    async with async_session() as s:
        a = Partner(raison_sociale=PREFIXE + "A", statut="actif", siret="11122233344455")
        b = Partner(raison_sociale=PREFIXE + "B", statut="actif")
        u = User(email=f"rel-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add_all([a, b, u])
        await s.flush()
        h = House(user_id=u.id, code_postal="83990", statut="proprietaire")
        s.add(h)
        await s.flush()

        def lead(p, moment, **kw):
            l = Lead(id=uuid.uuid4(), house_id=h.id, partner_id=p.id, type="travaux", metier="isolation", statut="transmis",
                     consent_client_at=moment, prix_ht=60, contact_nom=NOM_FOYER,
                     contact_email="foyer-secret@example.com", contact_telephone="0699999999", **kw)
            s.add(l)
            return l
        ids = {
            "a": a.id, "b": b.id, "user": u.id, "house": h.id,
            "debut": lead(a, a_paris(2025, 1, 1, 0, 30)).id,            # 31/12 23 h 30 UTC : janvier à Paris
            "attente": lead(a, a_paris(2025, 1, 15, 10)).id,
            "acceptee": lead(a, a_paris(2025, 1, 20, 10), facturable=False).id,
            "fin": lead(a, a_paris(2025, 1, 31, 23, 30)).id,             # 22 h 30 UTC : encore janvier
            "fevrier": lead(a, a_paris(2025, 2, 1, 0, 30)).id,           # 31/01 23 h 30 UTC : février
            "b1": lead(b, a_paris(2025, 1, 10, 9)).id,
        }
        await s.flush()
        s.add_all([Contestation(lead_id=ids["attente"], motif="doublon", commentaire="x", statut="en_attente"),
                   Contestation(lead_id=ids["acceptee"], motif="doublon", commentaire="x", statut="acceptee")])
        await s.commit()
        return ids


async def _effacer(ids) -> None:
    async with async_session() as s:
        for r in await s.scalars(select(Releve).where(Releve.mois == MOIS)):
            if r.pdf_path:
                Path(r.pdf_path).unlink(missing_ok=True)
        await s.execute(text("DELETE FROM releves WHERE mois = :m"), {"m": MOIS})
        await s.execute(text("DELETE FROM releves_clotures WHERE mois = :m"), {"m": MOIS})
        await s.execute(text("DELETE FROM leads WHERE house_id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM partners WHERE raison_sociale LIKE :p"), {"p": PREFIXE + "%"})
        await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids["user"]})
        await s.commit()


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent, migration 0039 non appliquée, ou janvier 2025 déjà clos")
        ids = client.portal.call(_creer)
        avant = settings.admin_token
        settings.admin_token = ADMIN["X-Admin-Token"]
        try:
            yield client, ids, {k: {"Authorization": f"Bearer {create_partner_token(str(ids[k]))}"} for k in ("a", "b")}
        finally:
            settings.admin_token = avant
            client.portal.call(lambda: _effacer(ids))
            client.portal.call(engine.dispose)


def _a(r):
    return next(x for x in r["releves"] if x["partenaire"]["raison_sociale"] == PREFIXE + "A")


def test_le_mois_provisoire_suit_les_leads_et_les_contestations(ctx):
    c, ids, _ = ctx
    r = c.get("/api/admin/releves", headers=ADMIN, params={"mois": MOIS}).json()
    assert r["statut"] == "provisoire" and r["cloture_possible_le"] == "2025-02-08"
    a = _a(r)
    lignes = {x["lead_id"]: x["etat"] for x in a["lignes"]}
    assert str(ids["debut"]) in lignes and str(ids["fin"]) in lignes and str(ids["fevrier"]) not in lignes
    assert lignes[str(ids["attente"])] == "contestation_en_cours"
    assert lignes[str(ids["acceptee"])] == "contestation_acceptee"
    assert (a["total_ht"], a["tva"], a["ttc"]) == (120.0, 24.0, 144.0)
    assert c.get("/api/admin/releves", headers=ADMIN, params={"mois": "2025-13"}).status_code == 400


def test_cloture_refusee_avant_le_8_et_avec_une_contestation_en_attente(ctx):
    c, ids, _ = ctx

    async def avant_le_8():
        async with async_session() as s:
            with pytest.raises(releves_lecture.ClotureRefusee, match="au plus tôt le 08/02/2025"):
                await releves_lecture.cloturer(s, MOIS, "test", aujourd_hui=date(2025, 2, 7))
    c.portal.call(avant_le_8)
    r = c.post(f"/api/admin/releves/{MOIS}/cloturer", headers=ADMIN)
    assert r.status_code == 409
    assert "1 contestation(s) encore en attente" in r.json()["detail"] and "83990" in r.json()["detail"]
    assert c.post(f"/api/admin/releves/{MOIS}/cloturer").status_code == 403


def test_cloture_puis_releve_immuable(ctx):
    c, ids, hp = ctx

    async def trancher_puis_modifier(apres_cloture: bool):
        async with async_session() as s:
            if not apres_cloture:
                cont = await s.scalar(select(Contestation).where(Contestation.lead_id == ids["attente"]))
                cont.statut = "refusee"
            else:
                l = await s.get(Lead, ids["debut"])
                l.facturable = False
                s.add(Lead(house_id=ids["house"], partner_id=ids["a"], type="travaux", metier="pac", statut="transmis",
                           consent_client_at=a_paris(2025, 1, 5, 12), prix_ht=60))
            await s.commit()
    c.portal.call(lambda: trancher_puis_modifier(False))
    r = c.post(f"/api/admin/releves/{MOIS}/cloturer", headers=ADMIN)
    assert r.status_code == 200 and r.json()["nb_releves"] == 2
    clos = c.get("/api/admin/releves", headers=ADMIN, params={"mois": MOIS}).json()
    assert clos["statut"] == "clos" and _a(clos)["total_ht"] == 180.0  # la contestation refusée compte

    # Ce qui change après la clôture ne touche plus le relevé.
    c.portal.call(lambda: trancher_puis_modifier(True))
    encore = c.get("/api/admin/releves", headers=ADMIN, params={"mois": MOIS}).json()
    assert _a(encore)["lignes"] == _a(clos)["lignes"] and _a(encore)["total_ht"] == 180.0
    assert c.post(f"/api/admin/releves/{MOIS}/cloturer", headers=ADMIN).status_code == 409

    # Le partenaire le voit clos, ne voit que le sien, et télécharge le PDF figé.
    mes = c.get("/api/partner/releves", headers=hp["a"]).json()
    jan = next(x for x in mes if x["mois"] == MOIS)
    assert jan["statut"] == "clos" and jan["total_ht"] == 180.0
    assert {x["mois"] for x in mes} >= {MOIS, "2025-02"}
    assert all(x["partenaire"]["raison_sociale"] == PREFIXE + "B" for x in c.get("/api/partner/releves", headers=hp["b"]).json())
    pdf = c.get(f"/api/partner/releves/{MOIS}/pdf", headers=hp["a"])
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    texte = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "ce document n'est pas une facture" in texte and "PROVISOIRE" not in texte
    for interdit in (NOM_FOYER, "foyer-secret@example.com", "0699999999"):
        assert interdit not in texte


def test_le_pdf_porte_la_mention_exacte_et_rien_du_foyer(ctx):
    c, _, hp = ctx
    pdf = c.get("/api/partner/releves/2025-02/pdf", headers=hp["a"])
    texte = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert " ".join(MENTION.split()) in " ".join(texte.split()) and "PROVISOIRE" in texte
    assert NOM_FOYER not in texte and "83990" in texte
    assert c.get("/api/partner/releves/2024-06/pdf", headers=hp["a"]).status_code == 404


def test_export_csv_sans_donnee_de_foyer(ctx):
    c, _, _ = ctx
    r = c.get(f"/api/admin/releves/{MOIS}/csv", headers=ADMIN)
    assert r.status_code == 200 and r.text.startswith("﻿mois;statut_releve;partenaire")
    assert PREFIXE + "A" in r.text and "60,00" in r.text and NOM_FOYER not in r.text


def test_rendu_direct_sans_police():
    """Le repli Helvetica (polices absentes) produit toujours la mention."""
    r = {"mois": MOIS, "partenaire": {"raison_sociale": "X", "siret": None}, "lignes": [], "nb_lignes": 0,
         "nb_facturables": 0, "en_attente": [], "total_ht": 0.0, "tva_taux": 0.2, "tva": 0.0, "ttc": 0.0}
    contenu = releve_pdf(r, "provisoire", fonts_dir=Path("/introuvable"))
    assert "pas une facture" in " ".join(p.extract_text() for p in PdfReader(io.BytesIO(contenu)).pages)
