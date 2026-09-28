"""Outillage commun des tests du simulateur.

AUCUN APPEL RÉSEAU : la production PVGIS est remplacée par une série fabriquée,
proportionnelle à la puissance crête — exactement comme l'est la vraie (PVGIS est
linéaire en `peakpower`), ce qui permet de tester la mise à l'échelle pour de bon.
"""

import math

import pytest

from app.services import simu_pv
from app.services.simu_types import Clim, Configuration, Lieu, Maison, Panneaux, Piscine, Stockage, Voiture

HEURES = 8760


def serie_1kwc_fictive() -> list[float]:
    """Cloche journalière modulée par la saison — l'allure d'une vraie série PVGIS."""
    serie = []
    for h in range(HEURES):
        jour, heure = h // 24, h % 24
        saison = 0.55 + 0.45 * math.sin((jour - 80) / 365 * 2 * math.pi)
        cloche = math.sin((heure - 6) / 14 * math.pi) if 6 <= heure <= 20 else 0.0
        serie.append(round(max(0.0, 0.62 * saison * cloche), 5))
    return serie


SERIE_1KWC = serie_1kwc_fictive()


@pytest.fixture
def pvgis_factice(monkeypatch):
    """Remplace l'appel PVGIS et compte les appels sortants (il doit y en avoir très peu)."""
    appels = []

    async def _faux_appel(*, lat, lon, peakpower, angle, aspect, loss):
        appels.append({"lat": lat, "lon": lon, "peakpower": peakpower,
                       "angle": angle, "aspect": aspect, "loss": loss})
        return [v * peakpower for v in SERIE_1KWC]

    monkeypatch.setattr("app.services.pvgis.production_series_hourly", _faux_appel)
    simu_pv.vider_cache()
    yield appels
    simu_pv.vider_cache()


def production_ref(nb_panneaux: int, nb_carport: int = 0) -> dict:
    """Ce que `simu_pv.production` renverrait, sans passer par le réseau."""
    from app.core.config import settings
    kwc = nb_panneaux * settings.simu_panneau_wc / 1000
    kwc_carport = nb_carport * settings.simu_panneau_wc / 1000
    total = [s * kwc for s in SERIE_1KWC]
    if nb_carport:
        total = [t + s * kwc_carport for t, s in zip(total, SERIE_1KWC)]
    return {
        "serie_toit_1kwc": SERIE_1KWC,
        "serie_carport_1kwc": SERIE_1KWC if nb_carport else None,
        "kwc_toit": kwc,
        "kwc_carport": kwc_carport,
        "kwc_total": kwc + kwc_carport,
        "total_h": total,
        "annuel_kwh": sum(total),
        "par_kwc_kwh": sum(SERIE_1KWC),
        "pertes_pct": 14.0,
    }


def maison_type(**kw) -> Maison:
    defauts = dict(
        surface_m2=110, nb_occupants=4, presence_journee="partielle",
        chauffage="elec_direct", ecs="ballon_elec",
        clim=Clim(present=True, deja_installe=True, nb_pieces=2),
        piscine=Piscine(present=True, deja_installe=True, volume_m3=40),
        voiture=Voiture(present=True, deja_installe=True, km_an=12000, recharge="nuit"),
        conso_connue_kwh_an=9000, puissance_souscrite_kva=9, raccordement="triphase",
    )
    defauts.update(kw)
    return Maison(**defauts)


def config_type(nb_panneaux: int = 14, maison: Maison | None = None, **stockage_kw) -> Configuration:
    return Configuration(
        lieu=Lieu(lat=43.30, lon=5.40, commune="Marseille"),
        maison=maison or maison_type(),
        panneaux=Panneaux(nb_panneaux=nb_panneaux, orientation="sud", inclinaison=30, ombrage="aucun"),
        stockage=Stockage(**stockage_kw),
    )
