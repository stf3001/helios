"""Le score de qualification d'une mise en relation (série 4, lot 2) — fonction pure.

Il se calcule À PARTIR DU DOSSIER FIGÉ, et de lui seul : un critère tiré de la fiche ne peut être
acquis que si le foyer a coché le résumé de la fiche, un projet que s'il l'a partagé. Le score ne
révèle donc rien que le dossier ne montre déjà.

Il est lu par le partenaire, ligne par ligne. Il ne change NI le prix, NI l'ordre des propositions,
NI l'accès du foyer aux mises en relation. Points dans `config.py` (`mer_score_points`).
"""
from datetime import date

from app.core.config import settings

LIBELLES = {
    "fiche_complete": "Fiche maison remplie à {pct:g} % ou plus",
    "projet_avance": "Projet à l'étude ou au stade des devis",
    "etude_recente": "Pré-audit ou étude de moins de {mois} mois partagé",
    "horizon_court": "Travaux envisagés dans les 6 mois",
    "budget_declare": "Budget envisagé indiqué",
    "telephone": "Téléphone fourni",
}


def _mois_avant(d: date, n: int) -> date:
    total = d.year * 12 + d.month - 1 - n
    annee, mois = divmod(total, 12)
    for jour in (d.day, 30, 29, 28):
        try:
            return date(annee, mois + 1, jour)
        except ValueError:
            continue
    raise AssertionError("inatteignable")


def score(dossier: dict, telephone: str | None, aujourd_hui: date) -> tuple[int, list[dict]]:
    fiche = dossier.get("fiche") or {}
    projet = dossier.get("projet") or {}
    etude = dossier.get("etude") or {}
    limite = _mois_avant(aujourd_hui, settings.mer_score_etude_max_mois).isoformat()
    acquis = {
        "fiche_complete": (fiche.get("completeness_score") or 0) >= settings.mer_score_fiche_min_pct,
        "projet_avance": projet.get("etape") in ("etude", "devis"),
        "etude_recente": bool(etude.get("date")) and etude["date"] >= limite,
        "horizon_court": fiche.get("horizon") == "<6mois",
        "budget_declare": fiche.get("budget_envisage") not in (None, "", "ne_sait_pas"),
        "telephone": bool((telephone or "").strip()),
    }
    detail = []
    for critere, points in settings.mer_score_points:
        detail.append({
            "critere": critere,
            "libelle": LIBELLES[critere].format(pct=settings.mer_score_fiche_min_pct,
                                                 mois=settings.mer_score_etude_max_mois),
            "points": points, "acquis": acquis[critere],
        })
    return sum(d["points"] for d in detail if d["acquis"]), detail
