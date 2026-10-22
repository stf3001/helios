"""Mises en relation, lot 1 : le parcours par l'API, CONTRE LA VRAIE BASE (sauté sans elle).

Quatre partenaires jetables, éligibles en isolation dans le Var (83), un sans charte et un
suspendu ; deux foyers (propriétaire, locataire). Tout est effacé en fin de module.
"""

import uuid
from collections import Counter
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token, create_partner_token
from app.main import app
from app.models.house import House
from app.models.partner import Partner
from app.models.user import User
from tests.outils_mer import assurer_charte, mettre_en_regle, retirer_charte

PREFIXE = "MER-TEST "
SIGNEE = datetime(2026, 10, 1, tzinfo=timezone.utc)


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT prix_ht FROM leads LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer() -> dict:
    async with async_session() as s:
        ids = {}
        ids["charte"] = await assurer_charte(s)
        for nom, statut, charte in [("A", "actif", SIGNEE), ("B", "actif", SIGNEE), ("C", "actif", SIGNEE),
                                    ("D", "actif", SIGNEE), ("Sans charte", "actif", None),
                                    ("Suspendu", "suspendu", SIGNEE)]:
            p = Partner(raison_sociale=PREFIXE + nom, statut=statut, charte_signee_at=charte, zones=["83"],
                        metiers=["isolation"], rge=True)
            s.add(p)
            await s.flush()
            # Lot 3 : « Sans charte » a ses justificatifs mais n'a pas signé la charte en vigueur.
            mettre_en_regle(s, p, ids["charte"][0])
            if charte is None:
                p.charte_version_signee = p.charte_signee_at = None
            ids[nom] = p.id
        for cle, statut in (("proprio", "proprietaire"), ("locataire", "locataire")):
            u = User(email=f"mer-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
            s.add(u)
            await s.flush()
            s.add(House(user_id=u.id, code_postal="83000", statut=statut))
            ids[cle] = u.id
        await s.commit()
        return ids


async def _effacer(ids) -> None:
    async with async_session() as s:
        await s.execute(text("DELETE FROM leads WHERE partner_id IN (SELECT id FROM partners WHERE raison_sociale LIKE :p)"),
                        {"p": PREFIXE + "%"})
        await s.execute(text("DELETE FROM partners WHERE raison_sociale LIKE :p"), {"p": PREFIXE + "%"})
        await retirer_charte(s, *ids["charte"])
        for cle in ("proprio", "locataire"):
            await s.execute(text("DELETE FROM houses WHERE user_id = :u"), {"u": ids[cle]})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids[cle]})
        await s.commit()


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0035 non appliquée")
        ids = client.portal.call(_creer)
        try:
            yield client, ids, {k: {"Authorization": f"Bearer {create_access_token(str(ids[k]))}"}
                                for k in ("proprio", "locataire")}
        finally:
            client.portal.call(lambda: _effacer(ids))
            client.portal.call(engine.dispose)


def _tester(nom):
    return nom.startswith(PREFIXE)


def test_propositions_tirees_au_sort_parmi_les_eligibles(ctx):
    c, ids, h = ctx
    vus = Counter()
    for _ in range(200):
        r = c.get("/api/leads/propositions", headers=h["proprio"],
                  params={"metier": "isolation"}).json()
        assert r["ordre"] == "tire_au_sort"
        noms = [p["raison_sociale"] for p in r["propositions"]]
        assert len(noms) <= 3
        vus.update(n for n in noms if _tester(n))
    # Les quatre éligibles apparaissent ; ni le partenaire sans charte, ni le suspendu.
    assert set(vus) == {PREFIXE + n for n in "ABCD"}
    assert c.get("/api/leads/propositions", headers=h["proprio"], params={"metier": "courtage"}).status_code == 400


def test_ad_solar_jamais_propose_hydrolia_et_eolia_portent_leur_lien(ctx):
    c, _, h = ctx
    for metier in ("solaire", "pac", "eau", "eolien"):
        noms = [p["raison_sociale"] for _ in range(20) for p in
                c.get("/api/leads/propositions", headers=h["proprio"], params={"metier": metier}).json()["propositions"]]
        assert "AD Solar" not in noms

    async def liens():
        async with async_session() as s:
            return dict((await s.execute(text(
                "SELECT raison_sociale, lien_interet FROM partners WHERE raison_sociale IN ('Hydrolia','Eolia','AD Solar')"
            ))).all()), (await s.scalar(text("SELECT statut FROM partners WHERE raison_sociale = 'AD Solar'")))
    lien, statut_ad = c.portal.call(liens)
    assert lien["Hydrolia"] == lien["Eolia"] == "Société créée par le fondateur d'Hélios"
    assert statut_ad == "suspendu"


def test_creation_garde_fous_et_prix_fige(ctx):
    c, ids, h = ctx
    creer = lambda qui, nom, **kw: c.post("/api/leads", headers=h[qui], json={
        "partner_id": str(ids[nom]), "type": "travaux", "metier": "isolation", "consent": True,
        "contact": {"nom": "Test", "email": "test@example.com"}, "creneaux": [{"jour": "lundi", "plage": "soir"}],
        **kw})

    r = creer("locataire", "A")
    assert r.status_code == 400 and r.json()["detail"] == "Ces travaux se décident avec votre propriétaire."
    assert creer("proprio", "Sans charte").status_code == 400
    assert creer("proprio", "A", consent=False).status_code == 400

    premier = creer("proprio", "A")
    assert premier.status_code == 201, premier.text
    assert "commission" not in premier.json()
    assert creer("proprio", "A").status_code == 400                 # doublon
    assert creer("proprio", "B").status_code == 201
    assert creer("proprio", "C").status_code == 201
    r = creer("proprio", "D")                                        # 4e demande active du métier
    assert r.status_code == 400 and "déjà 3 demandes" in r.json()["detail"]

    async def prix():
        async with async_session() as s:
            return (await s.execute(text("SELECT prix_ht, commission FROM leads WHERE id = :i"),
                                    {"i": premier.json()["id"]})).one()
    prix_ht, commission = c.portal.call(prix)
    assert float(prix_ht) == 60 and commission is None

    # Signé avec un montant : aucune commission n'est calculée sur un lead `travaux`.
    r = c.patch(f"/api/leads/{premier.json()['id']}/status", headers=h["proprio"],
                json={"statut": "signe", "montant_travaux": 12000})
    assert r.status_code == 200
    assert c.portal.call(prix)[1] is None
    # Une place se libère (le lead signé n'est plus actif) : le 4e passe.
    assert creer("proprio", "D").status_code == 201


def test_signer_la_charte_dans_l_espace_rend_le_partenaire_proposable(ctx):
    c, ids, h = ctx
    version = ids["charte"][0]
    hp = {"Authorization": f"Bearer {create_partner_token(str(ids['Sans charte']))}"}
    moi = c.get("/api/partner/me", headers=hp).json()
    assert moi["en_regle"] is False and moi["alertes"][0] == f"Signez la charte {version} pour recevoir de nouvelles demandes."
    assert c.post("/api/partner/charte", headers=hp, json={"version": "v0"}).status_code == 409
    r = c.post("/api/partner/charte", headers=hp, json={"version": version})
    assert r.status_code == 200 and r.json()["version_signee"] == version
    assert c.get("/api/partner/me", headers=hp).json()["en_regle"] is True
    vus = {p["raison_sociale"] for _ in range(60) for p in
           c.get("/api/leads/propositions", headers=h["proprio"], params={"metier": "isolation"}).json()["propositions"]}
    assert PREFIXE + "Sans charte" in vus
    # La route du lot 1 qui datait la charte à la place du partenaire n'existe plus.
    assert c.post(f"/api/admin/partners/{ids['Sans charte']}/charte", json={"date": "2026-10-01"}).status_code in (404, 405)
