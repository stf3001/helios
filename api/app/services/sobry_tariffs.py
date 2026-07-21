"""Grilles tarifaires SOBRY SoFlex / SoCap — GRILLE DE TEST fournie par l'utilisateur
(structure réelle des offres, valeurs à confirmer/mettre à jour auprès de SOBRY avant
toute décision commerciale, doc 09 §2).

SoFlex : tarif dynamique libre qui suit le marché de gros — plage observée entre -0,13
et 0,38 €/kWh, avec environ 1000 h/an à prix négatif (essentiellement les heures de
forte production solaire nationale, printemps/été, en milieu de journée).
SoCap : même dynamique de marché, mais plafonnée — jamais négative (plancher 0 €/kWh
au creux solaire de milieu de journée), jamais au-dessus de 0,25 €/kWh (les heures qui,
en SoFlex, montent jusqu'à 0,38 €/kWh sont ici plafonnées).

Le générateur ci-dessous produit une forme de courbe réaliste et déterministe (creux
solaire marqué au printemps/été en milieu de journée, pointes hiver matin/soir) calée
sur ces bornes et ce nombre d'heures négatives — ce n'est PAS la vraie série de prix
horaires SOBRY du jour (elle change en continu), c'est une grille de test pour estimer
l'ordre de grandeur d'un changement d'offre à consommation égale.
"""

import random

from app.core.config import settings

HOURS_PER_YEAR = 8760
_JOURS_PAR_MOIS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Indice solaire mensuel (0 = hiver sombre, 1 = plein été) — plus l'indice est haut, plus le
# creux de milieu de journée est marqué (surproduction solaire nationale sur le réseau).
_INDICE_SOLAIRE_MOIS = (0.05, 0.10, 0.30, 0.55, 0.80, 0.95, 1.00, 0.90, 0.65, 0.35, 0.10, 0.05)

# Profil horaire "demande" (0h→23h) : creux nuit, pointe matin, creux solaire midi, pointe soir.
_PROFIL_DEMANDE_24H = (
    0.30, 0.25, 0.20, 0.20, 0.25, 0.45, 0.70, 0.85,
    0.75, 0.55, 0.40, 0.30, 0.25, 0.30, 0.40, 0.55,
    0.70, 0.90, 1.00, 0.95, 0.80, 0.60, 0.45, 0.35,
)


def _raw_shape() -> list[float]:
    """Forme brute sans dimension (8760 points) : demande nette d'effet solaire + bruit
    reproductible (seed fixe → même grille de test à chaque appel, comparable dans le temps)."""
    rng = random.Random("sobry-tariffs-test-2026")
    shape: list[float] = []
    for mois in range(1, 13):
        indice_solaire = _INDICE_SOLAIRE_MOIS[mois - 1]
        for _jour in range(_JOURS_PAR_MOIS[mois - 1]):
            for h in range(24):
                demande = _PROFIL_DEMANDE_24H[h]
                # Creux solaire : marqué entre 10h et 16h, proportionnel à l'indice du mois.
                creux_solaire = indice_solaire * max(0.0, 1.0 - abs(h - 13) / 4.0)
                valeur = demande - 0.9 * creux_solaire + rng.uniform(-0.03, 0.03)
                shape.append(valeur)
    return shape


def _rescale_soflex(shape: list[float]) -> list[float]:
    """Reprojette la forme brute sur [prix_min, prix_max], pivot choisi pour ~N heures négatives."""
    n_negatives = settings.sobry_soflex_heures_negatives_an
    pivot = sorted(shape)[min(n_negatives, len(shape) - 1)]
    lo, hi = min(shape), max(shape)
    prix_min = settings.sobry_soflex_prix_min_eur_kwh
    prix_max = settings.sobry_soflex_prix_max_eur_kwh
    below_span = (pivot - lo) or 1.0
    above_span = (hi - pivot) or 1.0

    out = []
    for v in shape:
        prix = prix_min * (pivot - v) / below_span if v <= pivot else prix_max * (v - pivot) / above_span
        out.append(round(prix, 4))
    return out


def _rescale_socap(shape: list[float]) -> list[float]:
    """Reprojette la forme brute sur [0, prix_max] — jamais négatif, jamais au-dessus du plafond."""
    lo, hi = min(shape), max(shape)
    prix_max = settings.sobry_socap_prix_max_eur_kwh
    span = (hi - lo) or 1.0
    return [round(prix_max * (v - lo) / span, 4) for v in shape]


def hourly_prices(mode: str) -> list[float]:
    """Courbe de prix horaire annuelle (8760 points, EUR/kWh) pour 'soflex' ou 'socap'."""
    shape = _raw_shape()
    if mode == "soflex":
        return _rescale_soflex(shape)
    if mode == "socap":
        return _rescale_socap(shape)
    raise ValueError(f"Mode inconnu : {mode}")
