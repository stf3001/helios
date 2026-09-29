"""Generateur d'eau atmospherique — production et consommation, heure par heure.

CE QUI CHANGE PAR RAPPORT A `water_engine.py` : celui-ci travaille par VILLE, sur une
table de climat livree avec les donnees Hydrolia. Cette table est synthetique — trois
profils sinusoidaux pour douze villes, Toulouse ayant le climat de Strasbourg — et tous
culminent en AVRIL, minimum en octobre. Un AWG produit selon la chaleur et l'humidite :
placer l'ete au printemps fausse la saisonnalite, donc la production annuelle.

Ici le climat vient de PVGIS (endpoint TMY), comme la serie solaire : des releves reels,
heure par heure, en tout point du territoire. Et comme le simulateur raisonne deja en
8 760 heures, l'AWG s'y pose comme n'importe quel autre usage — sans regle speciale.

LES TABLES CONSTRUCTEUR, elles, restent la reference : generation en litres par jour et
consommation en kWh par litre, selon la temperature et l'humidite. Elles vivent dans
`api/data/hydrolia/` et ne sont pas publiees.
"""

from functools import lru_cache

from app.services.water_engine import _DATA, _interp, _load_table

#: Les trois modeles proposes au particulier. La gamme monte plus haut (250 L et au-dela)
#: mais releve du collectif — hors sujet pour une maison.
MODELES = ("20L", "50L", "100L")

HEURES = 8760


@lru_cache(maxsize=8)
def _table(modele: str, genre: str) -> dict[int, dict[int, float]]:
    """La table constructeur d'un modele : `generation` (L/jour) ou `consommation` (kWh/L)."""
    chemin = _DATA / f"{modele}_{genre}.csv"
    if not chemin.exists():
        raise FileNotFoundError(f"table {genre} absente pour le modele {modele}")
    return _load_table(chemin)


def tables_disponibles() -> bool:
    """Les tables constructeur sont-elles la ? Sans elles, on ne propose pas l'AWG."""
    return all((_DATA / f"{m}_{g}.csv").exists()
               for m in MODELES for g in ("generation", "consommation"))


def horaire(modele: str, temperature_h: list[float], humidite_h: list[float]) -> tuple[list[float], list[float]]:
    """(litres produits, kWh consommes) heure par heure, a pleine marche.

    La table de generation donne des litres par JOUR : a temperature et humidite donnees,
    la machine tourne au meme regime toute la journee, donc l'heure vaut le jour divise
    par 24. La table de consommation, elle, est deja par litre produit — pas de division.
    """
    gen = _table(modele, "generation")
    conso = _table(modele, "consommation")
    litres_h: list[float] = []
    kwh_h: list[float] = []
    for t, h in zip(temperature_h, humidite_h):
        litres = _interp(gen, t, h) / 24.0
        litres_h.append(litres)
        kwh_h.append(litres * _interp(conso, t, h))
    return litres_h, kwh_h


def sur_surplus(litres_h: list[float], kwh_h: list[float],
                surplus_h: list[float]) -> tuple[list[float], list[float], list[float]]:
    """La machine ne tourne QUE sur le surplus solaire.

    A chaque heure elle prend ce qu'il y a, et produit a proportion : demi-surplus, demie
    production. Rien n'est achete au reseau pour faire de l'eau, et le surplus qui serait
    parti au reseau pour quelques centimes devient des litres.

    Renvoie (litres, kWh consommes, surplus restant) — ce qui reste alimente ensuite la
    batterie et l'injection, dans cet ordre. L'AWG passe AVANT la batterie parce qu'il
    consomme sur-le-champ : stocker pour faire de l'eau plus tard ajouterait les pertes de
    la batterie a une operation deja couteuse en energie.
    """
    litres_reels: list[float] = []
    kwh_reels: list[float] = []
    reste: list[float] = []
    for litres, kwh, surplus in zip(litres_h, kwh_h, surplus_h):
        if kwh <= 0:
            litres_reels.append(0.0)
            kwh_reels.append(0.0)
            reste.append(surplus)
            continue
        part = min(1.0, max(0.0, surplus) / kwh)
        litres_reels.append(litres * part)
        kwh_reels.append(kwh * part)
        reste.append(max(0.0, surplus - kwh * part))
    return litres_reels, kwh_reels, reste
