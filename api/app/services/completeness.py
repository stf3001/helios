"""Score de complétude de la Fiche Maison — doc 02 §4.

Somme pondérée par bloc de la proportion de champs renseignés. code_postal est
requis dès la création de la fiche et n'entre donc pas dans le calcul. Les
champs libres/optionnels de chaque bloc (ex. chauffage d'appoint, PDL — phase 2)
n'y entrent pas non plus : le bloc Toiture (v1 promu, doc 09) est réservé au
simulateur solaire (J5) et n'est pas pondéré ici.
"""

from app.models.house import House

BLOCKS: dict[str, dict] = {
    "identite": {
        "weight": 20,
        "fields": [
            "type_logement", "statut", "annee_construction",
            "surface_habitable", "nb_niveaux", "nb_occupants", "residence_principale",
        ],
    },
    "enveloppe": {
        "weight": 25,
        "fields": [
            "isolation_combles", "isolation_murs", "isolation_plancher",
            "menuiseries", "ventilation", "dpe_lettre",
        ],
    },
    "systemes": {
        "weight": 25,
        "fields": ["chauffage_principal", "ecs", "clim", "regulation"],
    },
    "energie": {
        "weight": 15,
        "fields": ["conso_elec_kwh_an", "puissance_souscrite", "option_tarifaire"],
    },
    "projet": {
        "weight": 15,
        "fields": ["objectifs", "budget_envisage", "horizon"],
    },
}


def _is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    return True


def block_scores(house: House) -> dict[str, float]:
    """Pourcentage (0-100) de remplissage de chaque bloc."""
    result = {}
    for name, block in BLOCKS.items():
        fields = block["fields"]
        filled = sum(1 for f in fields if _is_filled(getattr(house, f)))
        result[name] = round(100 * filled / len(fields), 1)
    return result


def compute_score(house: House) -> float:
    total = 0.0
    for name, pct in block_scores(house).items():
        total += (pct / 100) * BLOCKS[name]["weight"]
    return round(total, 1)


def niveau_for_score(score: float) -> str:
    if score >= 70:
        return "preaudit_chiffre"
    if score >= 40:
        return "prediagnostic_qualitatif"
    return "conseils_generaux"
