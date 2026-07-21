"""Production photovoltaïque via PVGIS (Commission européenne, gratuit, sans clé) — doc 09 §1.

PVGIS PVcalc renvoie la production estimée (kWh) pour un point GPS, une orientation
(azimut/aspect), une inclinaison (angle) et une puissance crête (peakpower).
Convention aspect PVGIS : 0 = plein sud, -90 = est, +90 = ouest, 180 = nord.
"""

import httpx

_BASE = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
_BASE_SERIES = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
_SERIES_YEAR = 2019  # année non bissextile → exactement 8760 points, cohérent avec enedis_client

# Orientation texte → azimut PVGIS (degrés). Valeurs proposées par le formulaire du simulateur.
ORIENTATION_ASPECT: dict[str, int] = {
    "sud": 0,
    "sud_est": -45,
    "sud_ouest": 45,
    "est": -90,
    "ouest": 90,
    "nord_est": -135,
    "nord_ouest": 135,
    "nord": 180,
}

# Ombrage → pertes additionnelles (%) ajoutées aux pertes système de base.
OMBRAGE_LOSS: dict[str, float] = {"aucun": 0.0, "partiel": 10.0, "important": 25.0}

_BASE_SYSTEM_LOSS = 14.0  # pertes onduleur/câblage/salissure standard
_DEFAULT_ANGLE = 30       # inclinaison par défaut si non renseignée
PEAK_POWERS_KWC = (3, 6, 9)  # scénarios standard (doc 09 §1)


class PvgisError(Exception):
    pass


def _aspect_for(orientation: str | None) -> int:
    if orientation is None:
        return 0  # sud par défaut (hypothèse la plus favorable, signalée à l'utilisateur)
    return ORIENTATION_ASPECT.get(orientation, 0)


def _loss_for(ombrage: str | None) -> float:
    return _BASE_SYSTEM_LOSS + OMBRAGE_LOSS.get(ombrage or "aucun", 0.0)


def resolve_angle_aspect_loss(orientation: str | None, pente: int | None, ombrage: str | None) -> tuple[int, int, float]:
    """Traduit les champs de la fiche Maison (orientation/pente/ombrage) en paramètres PVGIS
    (angle, aspect, loss) — utilisé par `simulate` et par le simulateur Revolt (série horaire)."""
    angle = pente if pente is not None else _DEFAULT_ANGLE
    return angle, _aspect_for(orientation), _loss_for(ombrage)


async def production_for_power(
    *, lat: float, lon: float, peakpower: float, angle: int, aspect: int, loss: float
) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peakpower,
        "loss": loss,
        "angle": angle,
        "aspect": aspect,
        "outputformat": "json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(_BASE, params=params)
        if res.status_code != 200:
            raise PvgisError(f"PVGIS a renvoyé {res.status_code}")
        data = res.json()

    fixed = data["outputs"]
    return {
        "annual_kwh": round(fixed["totals"]["fixed"]["E_y"], 1),
        "monthly_kwh": [round(m["E_m"], 1) for m in fixed["monthly"]["fixed"]],
    }


async def production_series_hourly(
    *, lat: float, lon: float, peakpower: float, angle: int, aspect: int, loss: float
) -> list[float]:
    """Série de production PV heure par heure sur une année type (kWh), pour le simulateur
    "Revolt" (matching heure par heure avec une courbe de consommation). Endpoint PVGIS
    `seriescalc`, réel et gratuit (Commission européenne, pas de clé requise)."""
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peakpower,
        "loss": loss,
        "angle": angle,
        "aspect": aspect,
        "pvcalculation": 1,
        "startyear": _SERIES_YEAR,
        "endyear": _SERIES_YEAR,
        "outputformat": "json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.get(_BASE_SERIES, params=params)
        if res.status_code != 200:
            raise PvgisError(f"PVGIS (série horaire) a renvoyé {res.status_code}")
        data = res.json()

    hourly = data["outputs"]["hourly"]
    # "P" = puissance moyenne sur l'heure (W) → kWh sur ce pas d'une heure = P / 1000.
    return [round(point["P"] / 1000, 4) for point in hourly]


async def simulate(*, lat: float, lon: float, orientation: str | None, pente: int | None, ombrage: str | None) -> dict:
    """Production PVGIS pour 3 / 6 / 9 kWc au même emplacement/orientation."""
    angle, aspect, loss = resolve_angle_aspect_loss(orientation, pente, ombrage)

    by_power: dict[str, dict] = {}
    for power in PEAK_POWERS_KWC:
        by_power[str(power)] = await production_for_power(
            lat=lat, lon=lon, peakpower=power, angle=angle, aspect=aspect, loss=loss
        )

    return {
        "angle": angle,
        "aspect": aspect,
        "loss": loss,
        "by_power": by_power,  # clés "3", "6", "9" → {annual_kwh, monthly_kwh[12]}
    }
