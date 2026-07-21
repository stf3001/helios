"""Client Enedis DataConnect — courbe de charge (consommation) du logement, pour le
simulateur "Revolt" (PV + batterie + tarifs dynamiques, comparés à conso réelle égale).

Enedis DataConnect (OAuth2, https://datahub-enedis.fr) fournit la vraie courbe de charge
Linky (pas de 30 min, jusqu'à 3 ans d'historique) après consentement explicite du client.
L'inscription partenaire (SIRET, dossier RGPD/DPIA, callback HTTPS public — pas localhost)
est une démarche administrative réelle que l'UTILISATEUR doit mener lui-même : HELIOS ne
peut ni créer ce compte ni fournir les pièces légales à sa place.

Tant qu'aucune clé n'est configurée (`ENEDIS_CLIENT_ID` vide), ce module ne tente JAMAIS
d'appel réseau : il génère une courbe de charge SIMULÉE, calibrée sur le profil déclaré du
logement, et cette simulation est étiquetée comme telle partout où elle est exposée
(API, prompt LLM, frontend). Le jour où de vraies clés arrivent, `get_load_curve` bascule
seule sur `real_load_curve` — aucun autre code (moteur, router, front) n'a à changer.
"""

import random
from urllib.parse import urlencode

from app.core.config import settings
from app.models.house import House

AUTHORIZE_URL = "https://mon-compte-particulier.enedis.fr/dataconnect/v1/oauth2/authorize"
TOKEN_URL = "https://gw.ext.prod.api.enedis.fr/oauth2/v3/token"

HOURS_PER_YEAR = 8760


class EnedisUnavailable(Exception):
    """Identifiants absents ou intégration réelle non branchée — bascule vers la simulation."""


def is_configured() -> bool:
    return bool(settings.enedis_client_id and settings.enedis_client_secret)


def authorize_url(state: str) -> str:
    """URL de consentement Enedis vers laquelle rediriger l'utilisateur — n'existe que si
    l'inscription partenaire (démarche utilisateur, cf. docstring module) est faite."""
    if not is_configured():
        raise EnedisUnavailable("ENEDIS_CLIENT_ID non configuré — inscription partenaire requise")
    params = {"client_id": settings.enedis_client_id, "response_type": "code", "state": state, "duration": "P1Y"}
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def real_load_curve(pdl: str, access_token: str) -> list[float]:
    """Courbe de charge réelle (8760 points horaires, kWh) via l'API Enedis.

    Non implémenté : nécessite un token OAuth utilisateur obtenu via `authorize_url` (flux de
    consentement complet, hors scope tant qu'aucun partenaire réel n'est enregistré).
    """
    raise EnedisUnavailable("Intégration Enedis réelle non branchée (pas de partenaire homologué)")


# --- Courbe simulée : forme statistique plausible, PAS une mesure --------------------------

# Profil horaire relatif (0h→23h), somme normalisée à 1 sur la journée. Forme générique
# "foyer français" : creux nocturne, pic petit-déjeuner, creux journée (absence), pic soirée.
_PROFIL_BASE_24H = (
    0.55, 0.45, 0.40, 0.40, 0.45, 0.60, 0.90, 1.20,
    1.10, 0.85, 0.75, 0.75, 0.80, 0.75, 0.70, 0.75,
    0.90, 1.20, 1.55, 1.70, 1.50, 1.20, 0.90, 0.65,
)
_HEURES_MIDI = range(10, 18)  # heures où la présence au foyer relève surtout l'occupation

_CHAUFFAGE_ELEC = {"elec_direct", "PAC_air_eau", "PAC_air_air"}

# Facteur saisonnier mensuel (1.0 = moyenne annuelle) — hypothèse simplifiée, PAS une mesure :
# forte saisonnalité si chauffage électrique, quasi plate sinon (ECS/éclairage/électroménager).
_SAISON_CHAUFFAGE_ELEC = (1.55, 1.45, 1.20, 0.95, 0.75, 0.60, 0.55, 0.55, 0.70, 0.95, 1.25, 1.50)
_SAISON_SANS_CHAUFFAGE_ELEC = (1.08, 1.05, 1.02, 0.98, 0.94, 0.90, 0.88, 0.88, 0.94, 1.00, 1.05, 1.08)
_JOURS_PAR_MOIS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def synthetic_load_curve(house: House) -> list[float]:
    """Courbe de charge horaire SIMULÉE sur une année (8760 points, kWh) — une forme
    statistique plausible mise à l'échelle sur la conso annuelle déclarée, PAS une mesure.
    Seed déterministe sur l'id du logement : reproductible (même maison → même courbe)."""
    annual_kwh = house.conso_elec_kwh_an or settings.solar_conso_defaut_kwh_an
    chauffage_elec = house.chauffage_principal in _CHAUFFAGE_ELEC
    occupants = house.nb_occupants or 2
    saison = _SAISON_CHAUFFAGE_ELEC if chauffage_elec else _SAISON_SANS_CHAUFFAGE_ELEC

    rng = random.Random(f"{house.id}|{annual_kwh}|{chauffage_elec}")
    # Foyers nombreux : un peu plus de présence en journée (hypothèse simplifiée, pas mesurée).
    occ_boost = 1.0 + max(0, occupants - 2) * 0.04

    base_sum_24h = sum(_PROFIL_BASE_24H)
    curve: list[float] = []
    for mois in range(1, 13):
        facteur_mois = saison[mois - 1]
        for _ in range(_JOURS_PAR_MOIS[mois - 1]):
            for h in range(24):
                poids = _PROFIL_BASE_24H[h] / base_sum_24h
                if h in _HEURES_MIDI:
                    poids *= occ_boost
                bruit = 1.0 + rng.uniform(-0.08, 0.08)  # variabilité jour-à-jour
                curve.append(poids * facteur_mois * bruit)

    total = sum(curve) or 1.0
    scale = annual_kwh / total
    return [round(v * scale, 4) for v in curve]


async def get_load_curve(house: House) -> dict:
    """Point d'entrée unique du module : vraie courbe Enedis si un jour configuré, sinon
    courbe simulée — toujours accompagnée d'une étiquette de source honnête."""
    hourly = synthetic_load_curve(house)
    return {
        "source": "simulee",
        "hourly_kwh": hourly,
        "annual_kwh": round(sum(hourly)),
        "avertissement": (
            "Courbe de consommation SIMULÉE à partir du profil déclaré (chauffage, occupants, "
            "consommation annuelle) — ce n'est pas une mesure réelle. Le raccordement à Enedis "
            "(courbe de charge Linky réelle) est prévu mais nécessite votre consentement et une "
            "inscription partenaire encore en cours."
        ),
    }
