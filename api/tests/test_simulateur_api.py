"""Les deux points d'entrée publics, de bout en bout — sans réseau ni base de données.

PVGIS et le géocodage sont remplacés. Ce qui est vérifié ici : le câblage HTTP, la
validation stricte, la confidentialité de l'adresse pour un visiteur anonyme, et le
temps de réponse avec un cache chaud (les seuils sont des garde-fous de régression,
pas des mesures de performance).
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import simu_pv
from tests.conftest import SERIE_1KWC


@pytest.fixture
def client(monkeypatch):
    async def faux_pvgis(*, lat, lon, peakpower, angle, aspect, loss):
        return [v * peakpower for v in SERIE_1KWC]

    async def faux_geocode(adresse):
        return {"lat": 43.3012, "lon": 5.4013, "label": "12 rue Secrète 13001 Marseille",
                "commune": "Marseille", "code_postal": "13001", "citycode": "13201"}

    monkeypatch.setattr("app.services.pvgis.production_series_hourly", faux_pvgis)
    monkeypatch.setattr("app.services.geocoding.geocode", faux_geocode)
    simu_pv.vider_cache()
    with TestClient(app) as c:
        yield c
    simu_pv.vider_cache()


CONFIG = {
    "adresse": "12 rue Secrète, Marseille",
    "maison": {
        "surface_m2": 110, "nb_occupants": 4, "presence_journee": "partielle",
        "chauffage": "elec_direct", "ecs": "ballon_elec",
        "clim": {"present": True, "nb_pieces": 2},
        "conso_connue_kwh_an": 9000, "puissance_souscrite_kva": 9, "raccordement": "triphase",
    },
    "panneaux": {"nb_panneaux": 14, "orientation": "sud", "inclinaison": 30, "ombrage": "aucun"},
    "stockage": {"pilotage": True},
}


def test_calcul_repond_sans_compte(client):
    reponse = client.post("/api/simulateur/calcul", json=CONFIG)
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    for cle in ("indicateurs", "bilan_annuel", "bilan_mensuel", "journees",
                "stockage", "alertes", "hypotheses", "investissement"):
        assert cle in corps, cle
    assert len(corps["bilan_mensuel"]) == 12
    assert set(corps["journees"]) == {"printemps", "ete", "automne", "hiver"}
    assert all(len(points) == 24 for points in corps["journees"].values())


def test_l_adresse_complete_n_est_jamais_renvoyee(client):
    """Un visiteur anonyme ne doit récupérer que la commune et des coordonnées arrondies."""
    corps = client.post("/api/simulateur/calcul", json=CONFIG).json()
    assert corps["lieu"]["commune"] == "Marseille"
    assert "rue" not in str(corps["lieu"]).lower()
    assert corps["lieu"]["lat"] != 43.3012  # arrondi sur la grille
    assert abs(corps["lieu"]["lat"] - 43.3012) < 0.05


def test_un_champ_inconnu_est_refuse(client):
    """Mieux vaut une erreur qu'un réglage silencieusement ignoré."""
    mauvais = {**CONFIG, "panneaux": {**CONFIG["panneaux"], "nb_paneaux": 12}}
    assert client.post("/api/simulateur/calcul", json=mauvais).status_code == 422


def test_les_bornes_sont_appliquees(client):
    trop = {**CONFIG, "panneaux": {**CONFIG["panneaux"], "nb_panneaux": 500}}
    assert client.post("/api/simulateur/calcul", json=trop).status_code == 422


def test_sans_localisation_c_est_refuse(client):
    sans = {k: v for k, v in CONFIG.items() if k != "adresse"}
    assert client.post("/api/simulateur/calcul", json=sans).status_code == 422


def test_une_offre_virtuelle_inconnue_est_refusee(client):
    mauvais = {**CONFIG, "stockage": {"batterie_virtuelle": "offre-qui-n-existe-pas"}}
    assert client.post("/api/simulateur/calcul", json=mauvais).status_code == 400


def test_options_renvoie_les_trois_options(client):
    corps = client.post("/api/simulateur/options", json=CONFIG).json()
    assert {o["code"] for o in corps["options"]} == {
        "batterie_virtuelle", "batterie_physique", "pilotage"}
    assert corps["recommandee"] in {o["code"] for o in corps["options"]}
    assert len(corps["objectifs"]) == 5


def test_les_offres_declarent_leurs_contraintes(client):
    offres = client.get("/api/simulateur/offres").json()
    assert offres
    for offre in offres:
        assert offre["fournisseur_impose"], offre["code"]
        assert offre["note"]


def test_enregistrer_une_etude_demande_un_compte(client):
    reponse = client.post("/api/simulateur/etudes", json={"configuration": CONFIG})
    assert reponse.status_code in (401, 403)


def test_temps_de_reponse_avec_cache_chaud(client):
    """Garde-fou de régression. Objectifs du cahier des charges : 150 ms et 1,5 s."""
    client.post("/api/simulateur/calcul", json=CONFIG)  # amorce le cache PVGIS

    debut = time.perf_counter()
    for _ in range(3):
        assert client.post("/api/simulateur/calcul", json=CONFIG).status_code == 200
    calcul_ms = (time.perf_counter() - debut) / 3 * 1000

    debut = time.perf_counter()
    assert client.post("/api/simulateur/options", json=CONFIG).status_code == 200
    options_ms = (time.perf_counter() - debut) * 1000

    print(f"\n  /calcul  : {calcul_ms:.0f} ms (objectif 150)")
    print(f"  /options : {options_ms:.0f} ms (objectif 1500)")
    assert calcul_ms < 500, f"/calcul a pris {calcul_ms:.0f} ms"
    assert options_ms < 3000, f"/options a pris {options_ms:.0f} ms"


# --- Une seule maison pour les trois routes (revue du 19/10/2026) -----------------------
#
# `/calcul` passait l'éolienne et la machine à eau au moteur ; `/options` et `POST /etudes`
# non. L'étude enregistrée — celle que le chat relit — et les options portaient donc sur
# une autre maison que celle affichée. Ce test pose les deux équipements et exige les
# mêmes chiffres partout.

AVEC_VENT_ET_EAU = {
    **CONFIG,
    "eolien": {"kwc": 6},
    "eau": {"modele": "20L"},
}


class _FausseSession:
    """Juste ce que `POST /etudes` demande à la base : trouver la maison, garder l'étude."""

    def __init__(self):
        self.etudes = []

    async def scalar(self, _requete):
        from app.models.house import House
        return House(id="maison-test", user_id="user-test")

    def add(self, objet):
        self.etudes.append(objet)

    async def commit(self):
        pass

    async def refresh(self, objet):
        objet.id = "etude-test"


@pytest.fixture
def client_complet(client, monkeypatch):
    """Le client public, plus un climat simulé et un compte connecté sans base réelle."""
    from app.core.db import get_db
    from app.core.deps import get_current_user
    from app.models.user import User
    from app.services import awg, simu_climat

    if not awg.tables_disponibles():
        pytest.skip("Tables constructeur Hydrolia absentes : la machine à eau ne peut pas être chiffrée")

    async def faux_climat(*, lat, lon):
        heures = [h % 24 for h in range(8760)]
        return [14.0 + 8.0 * (h >= 10 and h <= 18) for h in heures], [70.0] * 8760

    monkeypatch.setattr("app.services.pvgis.climat_horaire", faux_climat)
    simu_climat.vider_cache()

    session = _FausseSession()

    async def faux_utilisateur():
        return User(id="user-test", email="test@helios.fr")

    async def fausse_db():
        yield session

    app.dependency_overrides[get_current_user] = faux_utilisateur
    app.dependency_overrides[get_db] = fausse_db
    yield client, session
    app.dependency_overrides.clear()
    simu_climat.vider_cache()


def test_calcul_options_et_etude_portent_sur_la_meme_maison(client_complet):
    client, session = client_complet

    calcul = client.post("/api/simulateur/calcul", json=AVEC_VENT_ET_EAU).json()
    sans = client.post("/api/simulateur/calcul", json=CONFIG).json()
    # Sinon le test ne prouverait rien : les deux équipements doivent peser.
    assert calcul["indicateurs"]["autonomie_pct"] != sans["indicateurs"]["autonomie_pct"]
    assert calcul["indicateurs"]["facture_mois_eur"] != sans["indicateurs"]["facture_mois_eur"]

    reponse = client.post("/api/simulateur/etudes", json={"configuration": AVEC_VENT_ET_EAU})
    assert reponse.status_code == 201, reponse.text
    etude = session.etudes[0].resultat["indicateurs"]

    options = client.post("/api/simulateur/options", json=AVEC_VENT_ET_EAU).json()
    # La configuration « actuelle » n'est exposée par `/options` qu'à travers ses objectifs.
    objectifs = {o["code"]: o["valeur"] for o in options["objectifs"]}

    ind = calcul["indicateurs"]
    assert etude["autonomie_pct"] == ind["autonomie_pct"]
    assert etude["facture_mois_eur"] == ind["facture_mois_eur"]
    assert objectifs["autonomie"] == f"{ind['autonomie_pct']:g} %"
    assert objectifs["facture"].startswith(f"{ind['facture_mois_eur']:g} € au lieu de")
    assert session.etudes[0].version_moteur == calcul["version_moteur"] == "simu-2"
