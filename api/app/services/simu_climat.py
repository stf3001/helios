"""Climat horaire du lieu — temperature et humidite, mises en cache.

Meme principe et memes protections que `simu_pv` : coordonnees ramenees sur une grille
pour ne pas marteler le serveur de la Commission europeenne, cache borne qui evince le
plus ancien, un verrou par cle pour que deux visiteurs d'une meme commune ne declenchent
qu'un seul appel.

La raison d'etre de ce module : le generateur d'eau atmospherique produit selon la
chaleur et l'humidite. Sans climat reel, son chiffrage ne vaut rien — et la table livree
avec les donnees Hydrolia place l'ete en avril (cf. `awg.py`).

L'appel est LOURD : PVGIS renvoie 1,2 Mo pour une annee type. D'ou le cache, et d'ou le
fait qu'on ne le declenche que si une machine a eau est posee.
"""

import asyncio
from collections import OrderedDict

from app.core.config import settings
from app.services import pvgis
from app.services.pvgis import PvgisError

#: (lat, lon) sur grille -> (temperatures, humidites)
_CACHE: "OrderedDict[tuple, tuple[list[float], list[float]]]" = OrderedDict()
_VERROUS: dict[tuple, asyncio.Lock] = {}


def vider_cache() -> None:
    """Utilise par les tests — jamais en production."""
    _CACHE.clear()
    _VERROUS.clear()


def taille_cache() -> int:
    return len(_CACHE)


def _sur_grille(valeur: float) -> float:
    pas = settings.simu_pvgis_pas_grille_deg
    return round(round(valeur / pas) * pas, 4)


async def climat(*, lat: float, lon: float) -> tuple[list[float], list[float]]:
    """Temperature (degres) et humidite relative (%) heure par heure, sur l'annee type."""
    cle = (_sur_grille(lat), _sur_grille(lon))
    if cle in _CACHE:
        _CACHE.move_to_end(cle)
        return _CACHE[cle]

    verrou = _VERROUS.setdefault(cle, asyncio.Lock())
    async with verrou:
        if cle in _CACHE:
            _CACHE.move_to_end(cle)
            return _CACHE[cle]
        try:
            donnees = await pvgis.climat_horaire(lat=cle[0], lon=cle[1])
        except PvgisError:
            # Meme piege que pour la serie solaire : le point ramene sur la grille peut
            # tomber en mer sur une commune littorale, et PVGIS refuse. On repart du point
            # exact ; le cache reste indexe sur la cle de grille.
            donnees = await pvgis.climat_horaire(lat=lat, lon=lon)

        _CACHE[cle] = donnees
        _CACHE.move_to_end(cle)
        while len(_CACHE) > settings.simu_pvgis_cache_max:
            _CACHE.popitem(last=False)
        return donnees
