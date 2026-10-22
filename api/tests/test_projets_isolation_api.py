"""Phase 2 : les projets « Isolation et confort » par l'API, CONTRE LA VRAIE BASE (sauté sans elle).

Même dispositif que `test_projets_api.py` : foyers jetables, effacés en fin de module.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.audit import Audit
from app.models.house import House
from app.models.user import User

COMBLES = {"action": "isolation_combles", "cout_eur": {"bas": 2730, "haut": 6370},
           "economie_annuelle_eur": {"bas": 255, "haut": 345, "central": 300},
           "statuts": {"cout_eur": "suppose", "economie_annuelle_eur": "calcule"}, "horizon": "maintenant"}


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT categorie_cil FROM travaux LIMIT 1"))
            await s.execute(text("SELECT 1 FROM projets LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer(statut: str, type_logement: str = "maison") -> uuid.UUID:
    async with async_session() as s:
        user = User(email=f"p2iso-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        house = House(user_id=user.id, code_postal="83000", statut=statut, type_logement=type_logement,
                      chauffage_principal="elec_direct")
        s.add(house)
        await s.flush()
        s.add(Audit(house_id=house.id, json_result={"priorites": [COMBLES]}))
        await s.commit()
        return user.id


async def _effacer(uids) -> None:
    async with async_session() as s:
        for uid in uids:
            h = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
            if h:
                await s.execute(text("DELETE FROM isolants WHERE travaux_id IN (SELECT id FROM travaux WHERE house_id = :h)"),
                                {"h": h})
                for table in ("audits", "journal_maison", "projets", "equipements", "travaux"):
                    await s.execute(text(f"DELETE FROM {table} WHERE house_id = :h"), {"h": h})
                await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": h})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        await s.commit()


async def _rubrique(travaux_id: str):
    async with async_session() as s:
        return await s.scalar(text("SELECT categorie_cil FROM travaux WHERE id = :t"), {"t": uuid.UUID(travaux_id)})


@pytest.fixture(scope="module")
def foyers():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent ou migration 0034 non appliquée")
        uids = {"proprio": client.portal.call(lambda: _creer_foyer("proprietaire")),
                "locataire": client.portal.call(lambda: _creer_foyer("locataire")),
                "appartement": client.portal.call(lambda: _creer_foyer("proprietaire", "appartement"))}
        try:
            yield client, {k: {"Authorization": f"Bearer {create_access_token(str(v))}"} for k, v in uids.items()}
        finally:
            client.portal.call(lambda: _effacer(uids.values()))
            client.portal.call(engine.dispose)


def _modeles(c, h):
    r = c.get("/api/houses/me/projets/modeles", headers=h).json()
    return r["familles"], {m["id"]: m for m in r["modeles"]}


def test_la_famille_et_les_visibilites(foyers):
    c, h = foyers
    familles, proprio = _modeles(c, h["proprio"])
    assert familles[-1] == "enveloppe"
    env = [i for i, m in proprio.items() if m["famille"] == "enveloppe"]
    assert env == ["isolation-combles", "isolation-murs", "isolation-plancher", "fenetres", "ventilation",
                   "regulation-chauffage"]
    assert proprio["isolation-combles"]["calcul"]["type"] == "audit"   # le pré-audit du foyer la chiffre
    assert proprio["isolation-murs"]["calcul"] is None and proprio["isolation-murs"]["outil_lien"] == "/espace/audits"
    assert proprio["regulation-chauffage"]["mention"] is None

    _, loc = _modeles(c, h["locataire"])
    assert [i for i, m in loc.items() if m["famille"] == "enveloppe"] == ["regulation-chauffage"]
    assert loc["regulation-chauffage"]["mention"] == "Les travaux sur le chauffage se décident avec votre propriétaire."

    _, app_ = _modeles(c, h["appartement"])
    assert [i for i, m in app_.items() if m["famille"] == "enveloppe"] == ["fenetres", "ventilation", "regulation-chauffage"]
    assert c.post("/api/houses/me/projets", headers=h["appartement"],
                  json={"modele_id": "isolation-combles"}).status_code == 400


def test_combles_lie_au_pre_audit_puis_termine_au_cil(foyers):
    c, h = foyers
    p = c.post("/api/houses/me/projets", headers=h["proprio"], json={"modele_id": "isolation-combles"}).json()
    assert p["modele"]["categorie_cil"] == "isolation_toiture"   # ce que « terminer » proposera
    lie = c.post(f"/api/houses/me/projets/{p['id']}/lier-etude", headers=h["proprio"]).json()
    assert (lie["budget_bas_eur"], lie["budget_haut_eur"], lie["economie_annuelle_eur"]) == (2730, 6370, 300)
    assert (lie["budget_source"], lie["budget_statut"], lie["economie_statut"]) == ("audit", "suppose", "calcule")
    assert lie["etude_ref"]["action"] == "isolation_combles"

    fini = c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h["proprio"],
                  json={"date_reception": date.today().isoformat(), "entreprise": "Isol Test"}).json()
    assert fini["etape"] == "termine"
    assert c.portal.call(lambda: _rubrique(fini["travaux_id"])) == "isolation_toiture"
    # Le carnet d'information du logement réclame alors les isolants de ce chantier.
    cil = c.get("/api/houses/me/cil", headers=h["proprio"]).json()
    bloc = next(b for b in cil if b["travaux_id"] == fini["travaux_id"])
    assert bloc["categorie_cil"] == "isolation_toiture"
    assert any("isolant" in m["champs"] for m in bloc["manques"])


def test_la_rubrique_se_retire_ou_se_refuse(foyers):
    c, h = foyers
    corps = {"date_reception": date.today().isoformat()}
    p = c.post("/api/houses/me/projets", headers=h["proprio"], json={"modele_id": "fenetres"}).json()
    assert c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h["proprio"],
                  json={**corps, "categorie_cil": "toiture"}).status_code == 400
    fini = c.post(f"/api/houses/me/projets/{p['id']}/terminer", headers=h["proprio"],
                  json={**corps, "categorie_cil": None}).json()
    assert c.portal.call(lambda: _rubrique(fini["travaux_id"])) is None

    v = c.post("/api/houses/me/projets", headers=h["proprio"], json={"modele_id": "ventilation"}).json()
    fini = c.post(f"/api/houses/me/projets/{v['id']}/terminer", headers=h["proprio"],
                  json={**corps, "equipements": [0]}).json()
    assert c.portal.call(lambda: _rubrique(fini["travaux_id"])) is None   # la VMC n'a pas de rubrique
    vmc = [e for e in c.get("/api/houses/me/equipements", headers=h["proprio"]).json() if e["type"] == "VMC_double"]
    assert len(vmc) == 1 and vmc[0]["origine_fiche"] == "ventilation"
