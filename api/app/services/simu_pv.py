"""Production photovoltaïque horaire du nouveau simulateur — une série PVGIS pour 1 kWc.

Principe : PVGIS n'est appelé qu'une fois par combinaison
(lieu arrondi, inclinaison, orientation, pertes), pour **1 kWc**. Toute puissance s'en
déduit par une multiplication — ajouter un panneau ne déclenche donc aucun appel réseau.

Deux protections, parce que `/api/simulateur/calcul` est PUBLIC et sans compte :
1. les coordonnées sont ramenées sur une grille (`simu_pvgis_pas_grille_deg`) — sinon
   n'importe qui peut faire varier la position au mètre près et nous faire marteler le
   serveur de la Commission européenne jusqu'à ce qu'il bloque notre adresse IP ;
2. le cache mémoire est borné (`simu_pvgis_cache_max`) et évince le plus ancien.

Le cache est en mémoire : il est vide après un redémarrage et n'est pas partagé entre
plusieurs processus. C'est assumé à ce stade — le passage en base est la prochaine étape
si la mise en production montre trop d'appels à froid.
"""

import asyncio
from collections import OrderedDict

from app.core.config import settings
from app.services import pvgis
from app.services.pvgis import PvgisError
from app.services.simu_types import Lieu, Panneaux

HEURES = 8760

# Orientation → azimut PVGIS (0 = sud, -90 = est, +90 = ouest).
ASPECTS = {"sud": 0, "sud_est": -45, "sud_ouest": 45, "est": -90, "ouest": 90}
# Est-Ouest : moitié est, moitié ouest — deux séries, moyennées.
ASPECTS_EST_OUEST = (-90, 90)

_CACHE: "OrderedDict[tuple, list[float]]" = OrderedDict()
_VERROUS: dict[tuple, asyncio.Lock] = {}


def vider_cache() -> None:
    """Utilisé par les tests — jamais en production."""
    _CACHE.clear()
    _VERROUS.clear()


def taille_cache() -> int:
    return len(_CACHE)


def _sur_grille(valeur: float) -> float:
    pas = settings.simu_pvgis_pas_grille_deg
    return round(round(valeur / pas) * pas, 4)


async def serie_1kwc(*, lat: float, lon: float, angle: int, aspect: int, loss: float) -> list[float]:
    """Série horaire (8 760 valeurs, kWh) produite par 1 kWc — mise en cache."""
    cle = (_sur_grille(lat), _sur_grille(lon), int(angle), int(aspect), round(loss, 1))
    if cle in _CACHE:
        _CACHE.move_to_end(cle)
        return _CACHE[cle]

    # Un verrou par clé : deux visiteurs sur la même commune au même instant ne
    # déclenchent qu'un seul appel sortant, pas deux.
    verrou = _VERROUS.setdefault(cle, asyncio.Lock())
    async with verrou:
        if cle in _CACHE:
            _CACHE.move_to_end(cle)
            return _CACHE[cle]
        try:
            serie = await pvgis.production_series_hourly(
                lat=cle[0], lon=cle[1], peakpower=1.0, angle=cle[2], aspect=cle[3], loss=cle[4]
            )
        except PvgisError:
            # Le point ramené sur la grille peut tomber EN MER sur une commune littorale :
            # le pas vaut ~5,5 km, et PVGIS refuse alors la requête (« Location over the
            # sea »). Vérifié sur Sanary-sur-Mer : 43,1196/5,8009 répond, 43,10/5,80 non.
            # On repart donc du point exact, sans grille. Le cache reste indexé sur la clé
            # de grille : le repli n'a lieu qu'une fois par commune concernée.
            serie = await pvgis.production_series_hourly(
                lat=lat, lon=lon, peakpower=1.0, angle=cle[2], aspect=cle[3], loss=cle[4]
            )
        if len(serie) != HEURES:
            raise PvgisError(f"PVGIS a renvoyé {len(serie)} points au lieu de {HEURES}")
        _CACHE[cle] = serie
        while len(_CACHE) > settings.simu_pvgis_cache_max:
            ancienne, _ = _CACHE.popitem(last=False)
            _VERROUS.pop(ancienne, None)
    _VERROUS.pop(cle, None)
    return serie


async def _serie_orientation(lieu: Lieu, orientation: str, angle: int, loss: float) -> list[float]:
    """Série pour 1 kWc selon l'orientation — Est-Ouest combine deux demi-champs."""
    if orientation == "est_ouest":
        est, ouest = await asyncio.gather(
            serie_1kwc(lat=lieu.lat, lon=lieu.lon, angle=angle, aspect=ASPECTS_EST_OUEST[0], loss=loss),
            serie_1kwc(lat=lieu.lat, lon=lieu.lon, angle=angle, aspect=ASPECTS_EST_OUEST[1], loss=loss),
        )
        return [(e + o) / 2 for e, o in zip(est, ouest)]
    aspect = ASPECTS.get(orientation, 0)
    return await serie_1kwc(lat=lieu.lat, lon=lieu.lon, angle=angle, aspect=aspect, loss=loss)


def kwc_de(nb_panneaux: int) -> float:
    return nb_panneaux * settings.simu_panneau_wc / 1000


def panneaux_max_du_toit(surface_m2: int | None) -> int | None:
    """« Remplir le toit » : combien de panneaux tiennent sur la surface exploitable."""
    if not surface_m2 or surface_m2 <= 0:
        return None
    return max(int(surface_m2 // settings.simu_panneau_surface_m2), 0)


async def production(lieu: Lieu, panneaux: Panneaux) -> dict:
    """Production horaire totale (toiture + carport) et les séries unitaires réutilisables.

    Renvoie aussi les séries pour 1 kWc : la recherche d'options ajoute des panneaux sans
    rappeler PVGIS, en multipliant simplement ces séries.
    """
    loss = pvgis.OMBRAGE_LOSS.get(panneaux.ombrage, 0.0) + 14.0  # pertes système de base
    taches = [_serie_orientation(lieu, panneaux.orientation, panneaux.inclinaison, loss)]
    carport_demande = panneaux.nb_panneaux_carport > 0
    if carport_demande:
        # Carport : plein sud, faible inclinaison — sa propre série.
        taches.append(
            serie_1kwc(
                lat=lieu.lat, lon=lieu.lon,
                angle=settings.simu_carport_pente_deg, aspect=0, loss=loss,
            )
        )
    series = await asyncio.gather(*taches)

    serie_toit_1kwc = series[0]
    serie_carport_1kwc = series[1] if carport_demande else None

    kwc_toit = kwc_de(panneaux.nb_panneaux)
    kwc_carport = kwc_de(panneaux.nb_panneaux_carport)
    total_h = [t * kwc_toit for t in serie_toit_1kwc]
    if serie_carport_1kwc is not None:
        total_h = [a + c * kwc_carport for a, c in zip(total_h, serie_carport_1kwc)]

    return {
        "total_h": total_h,
        "serie_toit_1kwc": serie_toit_1kwc,
        "serie_carport_1kwc": serie_carport_1kwc,
        "kwc_toit": kwc_toit,
        "kwc_carport": kwc_carport,
        "kwc_total": kwc_toit + kwc_carport,
        "pertes_pct": loss,
        "annuel_kwh": sum(total_h),
        "par_kwc_kwh": sum(serie_toit_1kwc),
    }


def recomposer(production_ref: dict, nb_panneaux: int) -> list[float]:
    """Production horaire pour un autre nombre de panneaux EN TOITURE, sans appel réseau.

    C'est ce qui rend la recherche d'options possible : on ne rappelle jamais PVGIS, on
    remultiplie la série de 1 kWc déjà obtenue. Le carport reste celui de la configuration
    de référence — la recherche d'options ne fait varier que la toiture, et une série de
    carport absente ne peut donc pas être demandée par erreur.
    """
    serie = [t * kwc_de(nb_panneaux) for t in production_ref["serie_toit_1kwc"]]
    carport = production_ref.get("serie_carport_1kwc")
    if carport is not None:
        kwc_carport = production_ref["kwc_carport"]
        serie = [a + c * kwc_carport for a, c in zip(serie, carport)]
    return serie
