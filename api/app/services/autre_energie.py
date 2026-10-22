"""La consommation déclarée d'une autre énergie que l'électricité, ramenée en kWh (pré-audit lot 7). Pur.

Un seul endroit pour la conversion : le pré-audit (`audit_engine.consommation`) et « Ce que
coûte ma maison » (`cout_maison.poste_autre_energie`) l'appellent tous les deux. Facteurs dans
`config.py` (`audit_kwh_par_unite`). Sans unité, ou avec un couple type-unité qui ne va pas
ensemble, la quantité ne sert pas : aucune unité n'est devinée.
"""
from app.core.config import settings
from app.schemas.house import UNITES_PAR_AUTRE_ENERGIE

# L'énergie du moteur (`ENERGIE_CHAUFFAGE`, `prix_energie`) que mesure chaque type déclaré.
ENERGIE_DU_TYPE: dict[str, str] = {
    "gaz": "gaz", "fioul": "fioul", "bois_buches": "bois", "granules": "bois", "reseau": "reseau",
}


def facteur(type_: str | None, unite: str | None) -> float | None:
    """kWh par unité, ou None si le couple n'est pas permis."""
    if unite not in UNITES_PAR_AUTRE_ENERGIE.get(type_, ()):
        return None
    return next((f for t, u, f in settings.audit_kwh_par_unite if (t, u) == (type_, unite)), None)


def kwh_autre_energie(type_: str | None, unite: str | None, qte: float | None) -> float | None:
    """La quantité déclarée en kWh, ou None (pas de quantité, pas d'unité, couple interdit)."""
    f = facteur(type_, unite)
    if f is None or not qte or qte <= 0:
        return None
    return qte * f
