"""Mises en relation, lot 5 : suivi côté foyer, bloc « À faire », écarts et indicateurs — contre la base de dev.

Deux partenaires jetables en règle (isolation, Var), un foyer propriétaire et ses demandes, posées
directement en base à des dates choisies. Tout est effacé en fin de module.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.db import async_session, engine
from app.core.security import create_access_token, create_partner_token
from app.main import app
from app.models.house import House
from app.models.partner import Lead, Partner
from app.models.user import User
from tests.outils_mer import assurer_charte, mettre_en_regle, retirer_charte

PREFIXE = "SUIVI-TEST "
ADMIN = {"X-Admin-Token": "secret-de-test-suivi"}


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT sans_contact_signale FROM leads LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer() -> dict:
    async with async_session() as s:
        charte = await assurer_charte(s)
        a = Partner(raison_sociale=PREFIXE + "A", statut="actif", zones=["83"], metiers=["isolation"], rge=True)
        b = Partner(raison_sociale=PREFIXE + "B", statut="actif", zones=["83"], metiers=["isolation"], rge=True)
        u = User(email=f"suivi-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add_all([a, b, u])
        await s.flush()
        mettre_en_regle(s, a, charte[0])
        mettre_en_regle(s, b, charte[0])
        h = House(user_id=u.id, code_postal="83000", statut="proprietaire")
        s.add(h)
        await s.flush()
        maintenant = datetime.now(timezone.utc)

        def lead(il_y_a_jours, **kw):
            champs = {"statut": "transmis", **kw}
            l = Lead(id=uuid.uuid4(), house_id=h.id, partner_id=a.id, type="travaux", metier="isolation",
                     consent_client_at=maintenant - timedelta(days=il_y_a_jours), prix_ht=60, **champs)
            s.add(l)
            return l.id
        ids = {"charte": charte, "a": a.id, "b": b.id, "user": u.id, "house": h.id,
               "ancien": lead(15), "recent": lead(1),
               "contredit": lead(20, statut="contacte", contacte_le=date.today() - timedelta(days=18), contact_foyer="non",
                                 sans_contact_signale=True)}
        await s.commit()
        return ids


async def _effacer(ids) -> None:
    async with async_session() as s:
        await s.execute(text("DELETE FROM reviews WHERE lead_id IN (SELECT id FROM leads WHERE house_id = :h)"),
                        {"h": ids["house"]})
        await s.execute(text("DELETE FROM leads WHERE house_id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM partners WHERE raison_sociale LIKE :p"), {"p": PREFIXE + "%"})
        await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": ids["house"]})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids["user"]})
        await retirer_charte(s, *ids["charte"])
        await s.commit()


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0040 non appliquée")
        ids = client.portal.call(_creer)
        avant = settings.admin_token
        settings.admin_token = ADMIN["X-Admin-Token"]
        try:
            yield client, ids, {"Authorization": f"Bearer {create_access_token(str(ids['user']))}"}
        finally:
            settings.admin_token = avant
            client.portal.call(lambda: _effacer(ids))
            client.portal.call(engine.dispose)


def _lead(c, h, lead_id):
    return next(l for l in c.get("/api/leads", headers=h).json() if l["id"] == str(lead_id))


def test_la_question_apparait_apres_5_jours_ouvres_et_dans_le_bloc_a_faire(ctx):
    c, ids, h = ctx
    assert _lead(c, h, ids["ancien"])["question_contact"] is True
    assert _lead(c, h, ids["recent"])["question_contact"] is False
    bloc = c.get("/api/houses/me/a-faire", headers=h).json()
    assert [q["lead_id"] for q in bloc["questions_contact"]] == [str(ids["ancien"])]
    assert bloc["questions_contact"][0]["partenaire"] == PREFIXE + "A" and bloc["rien_d_urgent"] is False


def test_non_puis_une_autre_entreprise_sans_ce_partenaire_et_le_prix_reste(ctx):
    c, ids, h = ctx
    r = c.post(f"/api/leads/{ids['ancien']}/contact", headers=h, json={"reponse": "non"})
    assert r.status_code == 200 and r.json()["sans_contact_signale"] is True and r.json()["question_contact"] is False
    assert c.post(f"/api/leads/{ids['ancien']}/contact", headers=h, json={"reponse": "oui"}).status_code == 409
    assert c.get("/api/houses/me/a-faire", headers=h).json()["questions_contact"] == []

    vus = {p["raison_sociale"] for _ in range(30) for p in c.get(
        "/api/leads/propositions", headers=h, params={"metier": "isolation", "exclure": str(ids["a"])}
    ).json()["propositions"] if p["raison_sociale"].startswith(PREFIXE)}
    assert vus == {PREFIXE + "B"}

    async def prix():
        async with async_session() as s:
            l = await s.get(Lead, ids["ancien"])
            return float(l.prix_ht), l.facturable, l.statut
    assert c.portal.call(prix) == (60.0, True, "transmis")


def test_declarations_du_foyer_sans_toucher_au_statut_du_partenaire(ctx):
    c, ids, h = ctx
    url = f"/api/leads/{ids['recent']}/declaration"
    assert c.post(url, headers=h, json={"type": "ailleurs"}).status_code == 422
    c.post(url, headers=h, json={"type": "devis_recu"})
    r = c.post(url, headers=h, json={"type": "travaux_signes"}).json()
    assert [d["type"] for d in r["declarations_foyer"]] == ["devis_recu", "travaux_signes"]
    assert r["statut"] == "transmis" and r["etape"] == "signee" and r["peut_noter"] is True
    c.post(url, headers=h, json={"type": "devis_recu"})   # une seule fois chaque déclaration
    assert len(_lead(c, h, ids["recent"])["declarations_foyer"]) == 2
    assert c.post(f"/api/leads/{ids['recent']}/review", headers=h, json={"note": 4}).status_code == 201
    # L'ancienne route qui écrivait dans le statut du partenaire n'existe plus.
    assert c.patch(f"/api/leads/{ids['recent']}/status", headers=h, json={"statut": "signe"}).status_code in (404, 405)


def test_ecarts_et_indicateurs_cote_administration(ctx):
    c, ids, h = ctx
    # Le partenaire déclare « sans suite » alors que le foyer a déclaré « travaux signés ».
    hp = {"Authorization": f"Bearer {create_partner_token(str(ids['a']))}"}
    assert c.patch(f"/api/partner/leads/{ids['recent']}/status", headers=hp,
                   json={"statut": "perdu", "motif_perdu": "Client injoignable"}).status_code == 200
    ecarts = {e["lead_id"]: e for e in c.get("/api/admin/mer/ecarts", headers=ADMIN).json()}
    assert ecarts[str(ids["contredit"])]["ecarts"][0]["sujet"] == "contact"
    assert ecarts[str(ids["recent"])]["ecarts"][0]["sujet"] == "signature"
    assert ecarts[str(ids["ancien"])]["ecarts"] == [] and ecarts[str(ids["ancien"])]["sans_contact_signale"] is True
    assert ecarts[str(ids["ancien"])]["prix_ht"] == 60 and ecarts[str(ids["ancien"])]["facturable"] is True
    assert c.get("/api/admin/mer/ecarts").status_code == 403

    ind = c.get("/api/admin/mer/indicateurs", headers=ADMIN).json()
    cumul = {i["cle"]: i for i in ind["cumul"]}
    assert set(cumul) >= {"transmises", "foyers_etude", "delai_contact", "non_contacte", "contestation",
                          "acceptation", "devis_partenaire", "devis_foyer", "signature_partenaire",
                          "signature_foyer", "note", "total_ht"}
    assert all(i["source"] in ("calculé", "déclaré partenaire", "déclaré foyer") for i in ind["cumul"])
    assert cumul["non_contacte"]["numerateur"] >= 2
