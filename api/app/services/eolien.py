"""Production eolienne domestique — l'eolienne Tulipe d'EOLIA, heure par heure.

D'OU VIENNENT LES CHIFFRES : le calculateur d'EOLIA (dossier `eolia`), repris tel quel
plutot que reinvente. Courbe de puissance mesuree sur le modele nominal de 6 kWc, mise a
l'echelle lineairement pour les autres puissances — c'est leur methode, on ne la corrige
pas. Profils de vent ERA5 horaires, donnes en km/h, par departement et par mois.

LA LIMITE A CONNAITRE : ERA5 ne couvre ici que DOUZE stations. Le simulateur, lui, sert
partout en France. On prend donc la station la plus proche a vol d'oiseau et on le DIT a
l'ecran — un visiteur de la Creuse doit savoir que son estimation vient de Lyon. C'est
aussi ce qui donne tout son sens au pret d'anemometre par EOLIA : un mois de mesure sur
le terrain vaut mieux que la station la moins loin.
"""

import json
import math
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

_DOSSIER = Path(__file__).resolve().parents[2] / "data" / "eolien"

#: Courbe de puissance de la Tulipe, relevee sur le modele nominal (cf. eolia).
VITESSES_MS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
PUISSANCES_KW = (0, 0, 0.05, 0.25, 0.6, 1.0, 1.6, 2.3, 3.0, 3.6, 4.2, 4.7, 5.0, 5.05, 5.0)
NOMINAL_KWC = 6.0

#: Jours par mois, annee non bissextile : le profil horaire d'un mois se repete a
#: l'identique sur chacun de ses jours. C'est la methode d'EOLIA.
JOURS_PAR_MOIS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
HEURES = 8760


@lru_cache(maxsize=1)
def _profils() -> dict:
    return json.loads((_DOSSIER / "profils_vent.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _stations() -> dict:
    return json.loads((_DOSSIER / "stations.json").read_text(encoding="utf-8"))


def station_la_plus_proche(lat: float, lon: float) -> tuple[str, str, float]:
    """(code departement, ville, distance en km) de la station ERA5 la plus proche.

    Distance a vol d'oiseau, formule de haversine. Douze stations pour la France
    entiere : la plus proche peut etre a 200 km, d'ou la distance renvoyee — l'ecran la
    montre, pour que personne ne prenne l'estimation pour une mesure locale.
    """
    meilleure: tuple[str, str, float] | None = None
    for code, station in _stations().items():
        if code not in _profils():
            continue
        d = _distance_km(lat, lon, station["lat"], station["lon"])
        if meilleure is None or d < meilleure[2]:
            meilleure = (code, station["city"], d)
    if meilleure is None:
        raise RuntimeError("aucune station de vent disponible")
    return meilleure


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rayon = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * rayon * math.asin(math.sqrt(a))


@lru_cache(maxsize=16)
def vitesses_horaires_ms(code_station: str) -> tuple[float, ...]:
    """Les 8760 vitesses de vent de l'annee, en m/s. Les donnees sont en km/h."""
    profil = _profils()[code_station]
    vitesses: list[float] = []
    for mois in range(1, 13):
        heures_du_mois = profil[str(mois)]
        jour = [heures_du_mois[str(h)] / 3.6 for h in range(24)]
        vitesses.extend(jour * JOURS_PAR_MOIS[mois - 1])
    return tuple(vitesses)


def puissance_kw(vitesse_ms: float, kwc: float) -> float:
    """Puissance instantanee, interpolee sur la courbe puis mise a l'echelle.

    La mise a l'echelle est LINEAIRE a partir du modele de 6 kWc : c'est la methode
    d'EOLIA. Au-dela du nominal on extrapole donc une courbe mesuree plus bas — une
    estimation a 9 kWc est moins sure qu'a 3.
    """
    if vitesse_ms <= VITESSES_MS[0]:
        brut = PUISSANCES_KW[0]
    elif vitesse_ms >= VITESSES_MS[-1]:
        brut = PUISSANCES_KW[-1]
    else:
        brut = 0.0
        for i in range(len(VITESSES_MS) - 1):
            x0, x1 = VITESSES_MS[i], VITESSES_MS[i + 1]
            if x0 <= vitesse_ms < x1:
                y0, y1 = PUISSANCES_KW[i], PUISSANCES_KW[i + 1]
                brut = y0 + (vitesse_ms - x0) * (y1 - y0) / (x1 - x0)
                break
    return brut * (kwc / NOMINAL_KWC)


def production_horaire(kwc: float, lat: float, lon: float,
                       facteur: float = 1.0) -> tuple[list[float], dict]:
    """Les 8760 kWh produits par l'eolienne, et d'ou vient l'estimation.

    `facteur` permet de recaler la production sur une mesure d'anemometre : EOLIA prete
    l'appareil un mois, et le rapport entre le vent mesure et le vent de la station donne
    ce coefficient. Sans mesure, il vaut 1.
    """
    if kwc <= 0:
        return [0.0] * HEURES, {}
    code, ville, distance = station_la_plus_proche(lat, lon)
    vitesses = vitesses_horaires_ms(code)
    serie = [puissance_kw(v * facteur, kwc) for v in vitesses]
    return serie, {
        "station": ville,
        "departement_station": code,
        "distance_km": round(distance),
        "vent_moyen_ms": round(sum(vitesses) / len(vitesses), 2),
    }


def cout_ttc_eur(kwc: float) -> int:
    """Tarif indicatif, interpole entre les deux bornes donnees par Stephane.

    6 900 EUR a 3 kWc, 12 000 EUR a 9 kWc, pose et demarches comprises, pour une distance
    de moins de 50 m entre le tableau et l'eolienne. Au-dela, EOLIA chiffre des options
    que l'outil ne connait pas — d'ou « indicatif », affiche comme tel.
    """
    bas_kwc, bas_eur = settings.simu_eolien_kwc_min, settings.simu_eolien_cout_min_eur
    haut_kwc, haut_eur = settings.simu_eolien_kwc_max, settings.simu_eolien_cout_max_eur
    if kwc <= bas_kwc:
        return bas_eur
    if kwc >= haut_kwc:
        return haut_eur
    part = (kwc - bas_kwc) / (haut_kwc - bas_kwc)
    return round(bas_eur + part * (haut_eur - bas_eur))
