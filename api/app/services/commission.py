"""Calcul de commission d'apport d'affaires — doc 08 §3 (grille indicative à calibrer par métier).

Déterministe : la commission = taux(métier) × montant HT des travaux signés. Le taux central
de la fourchette du doc est utilisé. Aucune valeur n'est produite par le LLM.
"""

# Taux de commission par métier (part du montant HT). Fourchettes doc 08 §3 → on prend le centre.
TAUX_PAR_METIER: dict[str, float] = {
    "pv": 0.05,          # photovoltaïque 4–6 %
    "photovoltaique": 0.05,
    "pac": 0.05,         # PAC / chauffage 4–6 %
    "chauffage": 0.05,
    "isolation": 0.065,  # isolation (ITE, combles) 5–8 %
    "menuiseries": 0.065,  # 5–8 %
    "vmc": 0.09,         # petits travaux 8–10 %
    "regulation": 0.09,
    "petits_travaux": 0.09,
}
_TAUX_DEFAUT = 0.06

# Forfait minimal pour les petits paniers (doc 08 : forfait 50–150 € sur < 3 k€).
_FORFAIT_MIN_EUR = 100
_SEUIL_PETIT_PANIER_EUR = 3000


def compute_commission(metier: str | None, montant_ht: int | None) -> float | None:
    """Commission sur travaux signés. None si le montant n'est pas encore renseigné."""
    if not montant_ht or montant_ht <= 0:
        return None
    taux = TAUX_PAR_METIER.get((metier or "").lower(), _TAUX_DEFAUT)
    commission = montant_ht * taux
    if montant_ht < _SEUIL_PETIT_PANIER_EUR:
        commission = max(commission, _FORFAIT_MIN_EUR)
    return round(commission, 2)
