"""Rendez-vous vus par l'équipe : filtrage, tuile du tableau de bord, et l'API d'administration.

Les tests d'API tournent CONTRE LA VRAIE BASE et se sautent sans elle (outillage de
`test_carnet_api.py`). Les rendez-vous de test sont posés à des minutes impaires, hors de
toute grille réelle, et effacés ensuite.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.rendez_vous import RendezVous
from app.models.user import User
from app.services import rdv_admin
from app.services.creneaux import a_paris
from tests.test_carnet_api import _base_prete, _creer_foyer, _effacer

MAINTENANT = a_paris(2026, 10, 26, 10, 0)  # lundi, premier jour de l'heure d'hiver


def _r(debut, statut="reserve", duree=30):
    return {"debut": debut, "duree_min": duree, "statut": statut}


def test_a_venir_du_plus_proche_et_l_appel_en_cours_y_reste():
    rdvs = [_r(MAINTENANT + timedelta(days=2)), _r(MAINTENANT + timedelta(hours=3)),
            _r(MAINTENANT - timedelta(minutes=10)),  # commencé il y a 10 min, fini dans 20 : en cours
            _r(MAINTENANT - timedelta(minutes=30))]  # fini à l'instant : passé
    a_venir = rdv_admin.filtrer(rdvs, "a_venir", MAINTENANT)
    assert [r["debut"] for r in a_venir] == [rdvs[2]["debut"], rdvs[1]["debut"], rdvs[0]["debut"]]
    assert rdv_admin.filtrer(rdvs, "passes", MAINTENANT) == [rdvs[3]]


def test_passes_sur_60_jours_du_plus_recent():
    rdvs = [_r(MAINTENANT - timedelta(days=d)) for d in (1, 59, 61, 5)]
    passes = rdv_admin.filtrer(rdvs, "passes", MAINTENANT)
    assert [(MAINTENANT - r["debut"]).days for r in passes] == [1, 5, 59]


def test_le_fuseau_de_paris_ne_decale_rien():
    """Vendredi 23/10 (été, UTC+2) et lundi 26/10 (hiver, UTC+1) : 9 h restent 9 h."""
    vendredi, lundi = a_paris(2026, 10, 23, 9, 0), a_paris(2026, 10, 26, 9, 0)
    tri = rdv_admin.filtrer([_r(lundi), _r(vendredi)], "a_venir", a_paris(2026, 10, 22, 12, 0))
    assert [r["debut"].hour for r in tri] == [9, 9] and tri[0]["debut"] == vendredi
    # Comparé en UTC (comme en base), l'ordre ne change pas.
    assert tri[0]["debut"].astimezone(timezone.utc) < tri[1]["debut"].astimezone(timezone.utc)


def test_tuile_du_tableau_de_bord():
    rdvs = [_r(MAINTENANT + timedelta(days=1)), _r(MAINTENANT + timedelta(hours=2), statut="annule"),
            _r(MAINTENANT + timedelta(days=3)), _r(MAINTENANT - timedelta(days=2)),
            _r(MAINTENANT - timedelta(days=4), statut="honore")]
    tuile = rdv_admin.resume_a_venir(rdvs, MAINTENANT)
    assert tuile["a_venir"] == 2  # l'annulé ne compte pas
    assert tuile["prochain"] == (MAINTENANT + timedelta(days=1)).isoformat()
    assert tuile["a_qualifier"] == 1  # passé, encore « réservé »
    assert rdv_admin.resume_a_venir([], MAINTENANT) == {"a_venir": 0, "prochain": None, "a_qualifier": 0}


# --- API, contre la vraie base ---


async def _admin_et_rdvs():
    maintenant = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    async with async_session() as s:
        admin = User(email=f"carnet-admin-{uuid.uuid4().hex[:8]}@test.invalid", password_hash="x", is_admin=True)
        s.add(admin)
        rdvs = [RendezVous(nom="Test Avenir", telephone="0600000001", debut=maintenant + timedelta(days=2, minutes=7)),
                RendezVous(nom="Test Passé", telephone="0600000002", debut=maintenant - timedelta(days=3, minutes=-7))]
        s.add_all(rdvs)
        await s.commit()
        return admin.id, [r.id for r in rdvs], rdvs[0].debut


async def _nettoyer(admin_id, rdv_ids):
    async with async_session() as s:
        await s.execute(delete(RendezVous).where(RendezVous.id.in_(rdv_ids)))
        await s.execute(delete(User).where(User.id == admin_id))
        await s.commit()


@pytest.fixture(scope="module")
def ctx():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent")
        admin_id, rdv_ids, debut_avenir = client.portal.call(_admin_et_rdvs)
        foyer = client.portal.call(_creer_foyer)
        contexte = {"c": client, "rdv_ids": [str(i) for i in rdv_ids], "debut_avenir": debut_avenir}
        try:
            yield contexte | {
                "admin": {"Authorization": f"Bearer {create_access_token(str(admin_id))}"},
                "foyer": {"Authorization": f"Bearer {create_access_token(str(foyer[0]))}"}}
        finally:
            client.portal.call(lambda: _nettoyer(admin_id, [uuid.UUID(i) for i in contexte["rdv_ids"]]))
            client.portal.call(lambda: _effacer([foyer[0]]))
            client.portal.call(engine.dispose)


def test_reserve_a_l_administration(ctx):
    c = ctx["c"]
    assert c.get("/api/admin/rendez-vous", headers=ctx["foyer"]).status_code == 403
    assert c.get("/api/admin/rendez-vous").status_code in (401, 403)
    assert c.patch(f"/api/admin/rendez-vous/{ctx['rdv_ids'][0]}", headers=ctx["foyer"],
                   json={"statut": "honore"}).status_code == 403


def test_a_venir_et_passes_par_l_api(ctx):
    c, h = ctx["c"], ctx["admin"]
    a_venir = c.get("/api/admin/rendez-vous", headers=h).json()
    passes = c.get("/api/admin/rendez-vous?periode=passes", headers=h).json()
    assert ctx["rdv_ids"][0] in [r["id"] for r in a_venir] and ctx["rdv_ids"][0] not in [r["id"] for r in passes]
    assert ctx["rdv_ids"][1] in [r["id"] for r in passes]
    debuts = [r["debut"] for r in a_venir]
    assert debuts == sorted(debuts, key=datetime.fromisoformat)
    assert c.get("/api/admin/rendez-vous?periode=hier", headers=h).status_code == 400


def test_statut_et_note_persistes(ctx):
    c, h, rid = ctx["c"], ctx["admin"], ctx["rdv_ids"][0]
    r = c.patch(f"/api/admin/rendez-vous/{rid}", headers=h, json={"statut": "absent", "note_interne": "  Messagerie, rappeler jeudi  "})
    assert r.status_code == 200 and r.json()["statut"] == "absent"
    ligne = [x for x in c.get("/api/admin/rendez-vous", headers=h).json() if x["id"] == rid][0]
    assert (ligne["statut"], ligne["note_interne"]) == ("absent", "Messagerie, rappeler jeudi")
    assert c.patch(f"/api/admin/rendez-vous/{rid}", headers=h, json={"statut": "perdu"}).status_code == 400
    assert c.patch(f"/api/admin/rendez-vous/{uuid.uuid4()}", headers=h, json={"statut": "honore"}).status_code == 404


def test_un_creneau_annule_redevient_reservable(ctx):
    """Décision du 21/10/2026 : l'index unique ne couvre plus les annulés (0029). Mais deux
    rendez-vous ACTIFS sur le même instant restent impossibles, et réactiver un annulé dont le
    créneau a été repris est refusé proprement (409)."""
    c, h, rid = ctx["c"], ctx["admin"], ctx["rdv_ids"][0]
    assert c.patch(f"/api/admin/rendez-vous/{rid}", headers=h, json={"statut": "annule"}).status_code == 200

    async def reserver(nom):
        async with async_session() as s:
            r = RendezVous(nom=nom, telephone="0600000003", debut=ctx["debut_avenir"])
            s.add(r)
            try:
                await s.commit()
                ctx["rdv_ids"].append(str(r.id))
                return "accepté"
            except Exception:
                await s.rollback()
                return "refusé"
    assert c.portal.call(lambda: reserver("Reprise")) == "accepté"
    assert c.portal.call(lambda: reserver("Doublon actif")) == "refusé"
    r = c.patch(f"/api/admin/rendez-vous/{rid}", headers=h, json={"statut": "reserve"})
    assert r.status_code == 409 and "repris" in r.json()["detail"]
    tableau = c.get("/api/admin/dashboard", headers=h).json()
    assert {"a_venir", "prochain", "a_qualifier"} <= set(tableau["rendez_vous"])
