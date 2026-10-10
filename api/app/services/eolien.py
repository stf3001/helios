"""Production eolienne domestique — l'eolienne Tulipe d'EOLIA, heure par heure.

D'OU VIENNENT LES CHIFFRES : le calculateur d'EOLIA (dossier `eolia`), repris tel quel
plutot que reinvente. Courbe de puissance mesuree sur le modele nominal de 6 kWc, mise a
l'echelle lineairement pour les autres puissances — c'est leur methode, on ne la corrige
pas. Profils de vent Meteo France, donnes en km/h, par departement, par mois et par heure.

CE QUE SONT CES PROFILS, ET CE QUE CA IMPOSE : des MOYENNES (288 valeurs par station,
repetees sur l'annee). Or la puissance d'une eolienne monte a peu pres comme le CUBE de
la vitesse : lire la courbe a la vitesse moyenne donne MOINS que ce que la machine
produit reellement, parce que les heures fortes rapportent plus que les heures faibles ne
coutent. On repartit donc le vent autour de sa moyenne selon une loi de Weibull k=2
(Rayleigh) avant de lire la courbe — la methode de reference du metier quand on ne
dispose que de la moyenne. Voir `puissance_attendue_kw`. Correction portee d'EOLIA le
10/10/2026, les deux calculateurs se tiennent a jour ENSEMBLE.

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
    """Puissance pour une vitesse INSTANTANEE, interpolee sur la courbe puis mise a
    l'echelle.

    La mise a l'echelle est LINEAIRE a partir du modele de 6 kWc : c'est la methode
    d'EOLIA. Au-dela du nominal on extrapole donc une courbe mesuree plus bas — une
    estimation a 9 kWc est moins sure qu'a 3.

    POUR UNE VITESSE MOYENNE, utiliser `puissance_attendue_kw` : nos profils de vent sont
    des moyennes, et lire la courbe a la moyenne sous-estime la production (cf. en-tete).
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


#: Facteur de forme de la loi de Weibull. 2 = loi de Rayleigh, la convention du metier
#: quand on ne dispose que de la vitesse moyenne. Plus k est grand, plus le vent est
#: regulier autour de sa moyenne, et moins la correction est forte.
#:
#: VERIFIE, PAS SUPPOSE (09/10/2026) : les douze stations ont ete comparees a de vraies
#: series de vent heure par heure (PVGIS, Commission europeenne, 2020) ramenees a la meme
#: moyenne annuelle. Sur l'ensemble des stations, k=2 tombe a 1 % de la production reelle.
#: Les k ajustes station par station vont de 1,6 a 2,8, mediane juste au-dessus de 2 :
#: la convention est la bonne, et un k par station n'apporterait rien de fiable.
WEIBULL_K = 2.0

_PAS_MS = 0.05          # pas d'integration ET pas de la table des moyennes
_VITESSE_MAX_MS = 40.0  # au-dela, la densite est nulle
_MOYENNE_MAX_MS = 25.0  # large, pour encaisser un coefficient d'anemometre


def _densite_weibull(v: float, echelle: float, k: float) -> float:
    return (k / echelle) * (v / echelle) ** (k - 1) * math.exp(-((v / echelle) ** k))


@lru_cache(maxsize=4)
def _table_attendue(k: float) -> tuple[float, ...]:
    """Table moyenne -> puissance attendue du modele nominal, construite une fois.

    L'integrale est la meme pour toutes les heures qui partagent la meme moyenne, et il y
    en a 8760 par simulation : la tabuler evite de refaire 8760 fois le meme travail.
    Construite DEPUIS la courbe de puissance — si la courbe change, la table suit, aucun
    nombre magique a maintenir.
    """
    echantillons = [_PAS_MS / 2 + i * _PAS_MS
                    for i in range(int(_VITESSE_MAX_MS / _PAS_MS))]
    puissances = [puissance_kw(v, NOMINAL_KWC) for v in echantillons]

    # Moyenne d'une Weibull d'echelle 1, mesuree sur la grille. C'est Gamma(1 + 1/k), mais
    # on l'integre plutot que de l'ecrire : pas de fonction speciale, et le resultat est
    # coherent avec la discretisation utilisee juste apres.
    moment = sum(v * _densite_weibull(v, 1.0, k) for v in echantillons)
    masse = sum(_densite_weibull(v, 1.0, k) for v in echantillons)
    moyenne_unitaire = moment / masse

    table = [0.0]
    for j in range(1, round(_MOYENNE_MAX_MS / _PAS_MS) + 1):
        echelle = (j * _PAS_MS) / moyenne_unitaire
        poids = [_densite_weibull(v, echelle, k) for v in echantillons]
        table.append(sum(p * w for p, w in zip(puissances, poids)) / sum(poids))
    return tuple(table)


def puissance_attendue_kw(moyenne_ms: float, kwc: float) -> float:
    """Puissance attendue quand `moyenne_ms` est une MOYENNE, pas une vitesse instantanee.

    C'est la fonction a appeler sur nos profils de vent, et sur une moyenne recalee par
    l'anemometre.

    ELLE NE REND PAS TOUJOURS PLUS que la courbe lue a la meme vitesse, et c'est normal :
    plus en dessous de ~6,8 m/s, ou la courbe est raide et bombee (les heures fortes
    rapportent plus que les faibles ne coutent), et moins au-dessus, ou la courbe
    s'aplatit vers son plateau. C'est pourquoi la correction vaut +56 % sur un site peu
    vente et seulement +8 % a Brest.
    """
    if moyenne_ms <= 0 or kwc <= 0:
        return 0.0
    table = _table_attendue(WEIBULL_K)
    if moyenne_ms >= _MOYENNE_MAX_MS:
        brut = table[-1]
    else:
        position = moyenne_ms / _PAS_MS
        i = int(position)
        brut = table[i] + (position - i) * (table[i + 1] - table[i])
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
    # Ce sont des MOYENNES : puissance ATTENDUE, pas puissance lue a la moyenne.
    serie = [puissance_attendue_kw(v * facteur, kwc) for v in vitesses]
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
