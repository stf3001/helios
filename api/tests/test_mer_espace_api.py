"""Mises en relation, lot 3 : espace partenaire, contestations, justificatifs, activation — contre la base de dev.

Deux partenaires jetables en isolation dans le Var, en règle ; un foyer propriétaire ; des
demandes posées directement en base. Tout est effacé en fin de module (fichiers compris).
"""
import json
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from app.core.config import settings
from app.core.db import async_session, engine
from app.core.security import create_access_token, create_partner_token
from app.main import app
from app.models.house import House
from app.models.partner import Lead, Partner, PartnerActivation, PartnerDocument
from app.models.user import User
from app.services.justificatifs import DOCS_DIR
from tests.outils_mer import assurer_charte, mettre_en_regle, retirer_charte

PREFIXE = "MER3-TEST "
EMAIL_CANDIDAT = f"mer3-{uuid.uuid4().hex[:8]}@example.com"
ADMIN = {"X-Admin-Token": "secret-de-test-mer3"}


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT facturable FROM leads LIMIT 1"))
            await s.execute(text("SELECT 1 FROM contestations LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer() -> dict:
    async with async_session() as s:
        charte = await assurer_charte(s)
        a = Partner(raison_sociale=PREFIXE + "A", statut="actif", zones=["83"], metiers=["isolation"], rge=True)
        b = Partner(raison_sociale=PREFIXE + "B", statut="actif", zones=["83"], metiers=["isolation"], rge=True)
        u = User(email=f"mer3-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add_all([a, b, u])
        await s.flush()
        mettre_en_regle(s, a, charte[0])
        mettre_en_regle(s, b, charte[0])
        h = House(user_id=u.id, code_postal="83000", statut="proprietaire")
        s.add(h)
        await s.flush()
        maintenant = datetime.now(timezone.utc)

        def lead(partner, il_y_a_jours, **kw):
            l = Lead(house_id=h.id, partner_id=partner.id, type="travaux", metier="isolation", statut="transmis",
                     consent_client_at=maintenant - timedelta(days=il_y_a_jours), prix_ht=60, **kw)
            s.add(l)
            return l
        recent, vieux, autre, refusable = lead(a, 1), lead(a, 8), lead(b, 1), lead(a, 2)
        await s.commit()
        return {"charte": charte, "a": a.id, "b": b.id, "user": u.id, "house": h.id, "recent": recent.id,
                "vieux": vieux.id, "autre": autre.id, "refusable": refusable.id}


async def _effacer(ids) -> None:
    async with async_session() as s:
        pids = list(await s.scalars(select(Partner.id).where(
            (Partner.raison_sociale.like(PREFIXE + "%")) | (Partner.email == EMAIL_CANDIDAT))))
        for d in await s.scalars(select(PartnerDocument).where(PartnerDocument.partner_id.in_(pids))):
            if d.path != "-" and DOCS_DIR in Path(d.path).parents:
                Path(d.path).unlink(missing_ok=True)
        for pid in pids:
            dossier = DOCS_DIR / str(pid)
            if dossier.is_dir() and not any(dossier.iterdir()):
                dossier.rmdir()
        await s.execute(text("DELETE FROM leads WHERE house_id = :h"), {"h": ids["house"]})
        if pids:
            await s.execute(text("DELETE FROM partners WHERE id = ANY(:p)"), {"p": pids})
        await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids["user"]})
        await retirer_charte(s, *ids["charte"])
        await s.commit()


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0038 non appliquée")
        ids = client.portal.call(_creer)
        settings_avant = settings.admin_token
        settings.admin_token = ADMIN["X-Admin-Token"]
        try:
            yield client, ids, {k: {"Authorization": f"Bearer {create_partner_token(str(ids[k]))}"} for k in ("a", "b")}
        finally:
            settings.admin_token = settings_avant
            client.portal.call(lambda: _effacer(ids))
            client.portal.call(engine.dispose)


def _facturable(c, lead_id):
    async def lire():
        async with async_session() as s:
            l = await s.get(Lead, lead_id)
            return l.facturable, float(l.prix_ht)
    return c.portal.call(lire)


def test_un_partenaire_ne_voit_que_ses_demandes(ctx):
    c, ids, hp = ctx
    mes = {l["id"] for l in c.get("/api/partner/leads", headers=hp["a"]).json()}
    assert str(ids["recent"]) in mes and str(ids["autre"]) not in mes
    assert c.get(f"/api/partner/leads/{ids['autre']}", headers=hp["a"]).status_code == 404
    assert c.post(f"/api/partner/leads/{ids['autre']}/contestation", headers=hp["a"],
                  json={"motif": "doublon", "commentaire": "x"}).status_code == 404


def test_contestation_dans_le_delai_puis_acceptee(ctx):
    c, ids, hp = ctx
    url = f"/api/partner/leads/{ids['recent']}/contestation"
    assert c.get(f"/api/partner/leads/{ids['recent']}", headers=hp["a"]).json()["peut_contester"] is True
    r = c.post(url, headers=hp["a"], json={"motif": "doublon", "commentaire": "Déjà client depuis mars"})
    assert r.status_code == 201 and r.json()["statut"] == "en_attente"
    assert c.post(url, headers=hp["a"], json={"motif": "doublon", "commentaire": "encore"}).status_code == 400
    assert c.get(f"/api/partner/leads/{ids['recent']}", headers=hp["a"]).json()["peut_contester"] is False

    file = c.get("/api/admin/contestations", headers=ADMIN).json()
    mienne = next(x for x in file if x["lead"]["id"] == str(ids["recent"]))
    assert mienne["libelle"].startswith("Doublon")
    assert mienne["doublons_helios_12_mois"] == 2  # « vieux » (J-8) et « refusable » (J-2), transmis avant
    assert c.post(f"/api/admin/contestations/{mienne['id']}/decision", json={"acceptee": True, "motif": "ok"}
                  ).status_code == 403
    d = c.post(f"/api/admin/contestations/{mienne['id']}/decision", headers=ADMIN,
               json={"acceptee": True, "motif": "Doublon confirmé par le partenaire"})
    assert d.status_code == 200 and d.json()["facturable"] is False
    assert _facturable(c, ids["recent"]) == (False, 60.0)  # prix gardé, plus facturable
    assert c.post(f"/api/admin/contestations/{mienne['id']}/decision", headers=ADMIN,
                  json={"acceptee": False, "motif": "deux fois"}).status_code == 409


def test_contestation_refusee_ne_change_rien(ctx):
    c, ids, hp = ctx
    essais = [(date.today() - timedelta(days=1)).isoformat()] * 2 + [date.today().isoformat()]
    r = c.post(f"/api/partner/leads/{ids['refusable']}/contestation", headers=hp["a"],
               json={"motif": "injoignable", "commentaire": "Trois appels sans réponse", "essais": essais})
    assert r.status_code == 201 and len(r.json()["essais"]) == 3
    cid = next(x["id"] for x in c.get("/api/admin/contestations", headers=ADMIN).json()
               if x["lead"]["id"] == str(ids["refusable"]))
    d = c.post(f"/api/admin/contestations/{cid}/decision", headers=ADMIN,
               json={"acceptee": False, "motif": "Les créneaux du foyer n'ont pas été respectés"})
    assert d.json() == {"id": cid, "statut": "refusee", "facturable": True}
    assert _facturable(c, ids["refusable"]) == (True, 60.0)


def test_contestation_refusee_apres_7_jours(ctx):
    c, ids, hp = ctx
    assert c.get(f"/api/partner/leads/{ids['vieux']}", headers=hp["a"]).json()["peut_contester"] is False
    r = c.post(f"/api/partner/leads/{ids['vieux']}/contestation", headers=hp["a"],
               json={"motif": "coordonnees_fausses", "commentaire": "Numéro inexistant"})
    assert r.status_code == 400 and "délai de 7 jours" in r.json()["detail"]


def test_le_suivi_declaratif_ne_touche_pas_au_prix(ctx):
    c, ids, hp = ctx
    url = f"/api/partner/leads/{ids['vieux']}/status"
    hier = (date.today() - timedelta(days=1)).isoformat()
    r = c.patch(url, headers=hp["a"], json={"statut": "contacte", "contacte_le": hier})
    assert r.status_code == 200 and r.json()["contacte_le"] == hier
    assert c.patch(url, headers=hp["a"], json={"statut": "devis"}).json()["montant_travaux"] is None
    assert c.patch(url, headers=hp["a"], json={"statut": "perdu"}).status_code == 400  # motif obligatoire
    futur = (date.today() + timedelta(days=1)).isoformat()
    assert c.patch(url, headers=hp["a"], json={"statut": "contacte", "contacte_le": futur}).status_code == 400
    r = c.patch(url, headers=hp["a"], json={"statut": "signe", "montant_travaux": 15000})
    assert r.json()["facturable"] is True and _facturable(c, ids["vieux"]) == (True, 60.0)


def test_justificatif_expire_sort_des_propositions_mais_garde_les_demandes(ctx):
    c, ids, hp = ctx

    async def foyer_et_expiration():
        async with async_session() as s:
            await s.execute(update(PartnerDocument).where(PartnerDocument.partner_id == ids["b"],
                                                          PartnerDocument.type == "decennale")
                            .values(date_fin=date.today() - timedelta(days=1)))
            await s.commit()
    c.portal.call(foyer_et_expiration)
    foyer = {"Authorization": f"Bearer {create_access_token(str(ids['user']))}"}
    vus = {p["raison_sociale"] for _ in range(40) for p in
           c.get("/api/leads/propositions", headers=foyer, params={"metier": "isolation"}).json()["propositions"]}
    assert PREFIXE + "A" in vus and PREFIXE + "B" not in vus
    assert [l["id"] for l in c.get("/api/partner/leads", headers=hp["b"]).json()] == [str(ids["autre"])]
    moi = c.get("/api/partner/me", headers=hp["b"]).json()
    assert moi["en_regle"] is False and any("décennale expiré" in a for a in moi["alertes"])
    # Le nouveau dépôt le remet dans les propositions.
    r = c.post("/api/partner/documents", headers=hp["b"],
               data={"type": "decennale", "date_fin": (date.today() + timedelta(days=300)).isoformat()},
               files={"fichier": ("decennale.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert r.status_code == 201
    assert c.get("/api/partner/me", headers=hp["b"]).json()["en_regle"] is True
    # Un justificatif refusé par l'administration ne compte plus.
    assert c.post(f"/api/admin/partners/{ids['b']}/documents/{r.json()['id']}/refuser", headers=ADMIN,
                  json={"motif": "Illisible"}).status_code == 200
    assert c.get("/api/partner/me", headers=hp["b"]).json()["en_regle"] is False


def test_depot_refuse_si_dates_ou_format_invalides(ctx):
    c, _, hp = ctx
    vieux_kbis = (date.today() - timedelta(days=120)).isoformat()
    r = c.post("/api/partner/documents", headers=hp["a"], data={"type": "kbis", "date_delivrance": vieux_kbis},
               files={"fichier": ("k.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 400 and "moins de 3 mois" in r.json()["detail"]
    r = c.post("/api/partner/documents", headers=hp["a"],
               data={"type": "rge", "date_fin": (date.today() + timedelta(days=9)).isoformat()},
               files={"fichier": ("r.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 400


def _candidature(c, **kw):
    champs = {"raison_sociale": PREFIXE + "Candidat", "siret": "12345678901234", "email": EMAIL_CANDIDAT,
              "rge": False, "zones": ["83"], "metiers": ["isolation"]}
    champs.update(kw)
    return c.post("/api/partners/apply",
                  data={"candidature": json.dumps(champs), "kbis_date": date.today().isoformat(),
                        "decennale_fin": (date.today() + timedelta(days=200)).isoformat()},
                  files={"kbis": ("kbis.pdf", b"%PDF-1.4 kbis", "application/pdf"),
                         "decennale": ("dec.pdf", b"%PDF-1.4 dec", "application/pdf")})


def test_candidature_validation_et_lien_d_activation_a_usage_unique(ctx):
    c, _, _ = ctx
    assert _candidature(c, rge=True).status_code == 400          # RGE déclaré sans pièce
    r = _candidature(c)
    assert r.status_code == 201, r.text
    assert _candidature(c).status_code == 409                      # même e-mail
    pid = r.json()["id"]
    fiche = next(p for p in c.get("/api/admin/partners", headers=ADMIN).json() if p["id"] == pid)
    assert {d["type"] for d in fiche["documents"]} == {"kbis", "decennale"} and fiche["en_regle"] is False

    lien = c.post(f"/api/admin/partners/{pid}/activate", headers=ADMIN).json()
    assert lien["lien"].startswith("/partenaire/activer?jeton=")
    jeton = lien["lien"].split("jeton=")[1]
    assert c.get("/api/partner/activation", params={"jeton": jeton}).json()["email"] == EMAIL_CANDIDAT
    r = c.post("/api/partner/activation", json={"jeton": jeton, "password": "MotDePasse-2026"})
    assert r.status_code == 200 and r.json()["access_token"]
    assert c.post("/api/partner/activation", json={"jeton": jeton, "password": "Autre-2026xx"}).status_code == 410
    assert c.post("/api/partner/login", json={"email": EMAIL_CANDIDAT, "password": "MotDePasse-2026"}).status_code == 200

    # Un nouveau lien invalide le précédent ; un lien expiré ne sert plus.
    l1 = c.post(f"/api/admin/partners/{pid}/lien-activation", headers=ADMIN).json()["lien"].split("jeton=")[1]
    l2 = c.post(f"/api/admin/partners/{pid}/lien-activation", headers=ADMIN).json()["lien"].split("jeton=")[1]
    assert c.get("/api/partner/activation", params={"jeton": l1}).status_code == 410

    async def expirer():
        async with async_session() as s:
            await s.execute(update(PartnerActivation).where(PartnerActivation.partner_id == uuid.UUID(pid))
                            .values(expire_le=datetime.now(timezone.utc) - timedelta(seconds=1)))
            await s.commit()
    c.portal.call(expirer)
    assert c.get("/api/partner/activation", params={"jeton": l2}).status_code == 410
    assert settings.mer_activation_jours == 7


def test_refus_motive_d_une_candidature(ctx):
    c, ids, _ = ctx
    assert c.post(f"/api/admin/partners/{ids['a']}/refuser", headers=ADMIN, json={"motif": "Test"}).status_code == 409
    r = _candidature(c, email=f"x{EMAIL_CANDIDAT}", raison_sociale=PREFIXE + "Refusé")
    pid = r.json()["id"]
    d = c.post(f"/api/admin/partners/{pid}/refuser", headers=ADMIN, json={"motif": "Kbis illisible"})
    assert d.json()["statut"] == "refuse" and d.json()["motif_refus"] == "Kbis illisible"
    assert c.post(f"/api/admin/partners/{pid}/activate", headers=ADMIN).status_code == 409


def test_echeances_a_30_jours(ctx):
    c, ids, _ = ctx
    lignes = [l for l in c.get("/api/admin/justificatifs/echeances", headers=ADMIN).json()
              if l["partner_id"] == str(ids["b"])]
    assert lignes and all(l["etat"] in ("expire", "manquant", "bientot") for l in lignes)
