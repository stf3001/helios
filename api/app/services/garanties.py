"""Garanties et âge des équipements — fonctions pures, sans accès à la base (carnet, lot 1).

Les durées de chantier (1, 2 et 10 ans depuis la réception) sont celles du Code civil ;
elles sont affichées avec une mention de vérification, jamais comme acquises : le contrat
et l'attestation d'assurance de l'entreprise font foi. Aucun texte d'explication ici —
l'écran renvoie à la fiche `kb/garanties_travaux.md`.

Statut des données : `declare` (saisi par le foyer), `calcule` (déduit d'une date exacte),
`suppose` (déduit d'une année seule, posée au 1er juillet). Ce statut accompagne chaque
chiffre jusqu'à l'écran.
"""
from datetime import date

# Une seule source pour les trois garanties : code, libellé, durée en années.
GARANTIES_CHANTIER = (
    ("parfait_achevement", "Parfait achèvement", 1),
    ("bon_fonctionnement", "Bon fonctionnement", 2),
    ("decennale", "Décennale", 10),
)

JOURS_BIENTOT = 60
MENTION_VERIFICATION = "À vérifier sur votre contrat et l'attestation d'assurance de l'entreprise"


def ajouter_annees(d: date, n: int) -> date:
    """Même jour, n ans plus tard ; un 29 février tombe au 28 les années non bissextiles."""
    try:
        return d.replace(year=d.year + n)
    except ValueError:
        return d.replace(year=d.year + n, day=28)


def fin_garanties_chantier(date_reception: date) -> list[dict]:
    return [
        {"code": code, "libelle": libelle, "duree_ans": ans, "fin": ajouter_annees(date_reception, ans)}
        for code, libelle, ans in GARANTIES_CHANTIER
    ]


def statut_garantie(fin: date, aujourd_hui: date) -> str:
    """`expiree` le lendemain de la fin ; `bientot` de J-60 au jour de la fin inclus."""
    reste = (fin - aujourd_hui).days
    if reste < 0:
        return "expiree"
    return "bientot" if reste <= JOURS_BIENTOT else "en_cours"


def _champ(obj, nom):
    """Lit un attribut d'un modèle SQLAlchemy comme une clé de dict (tests, scripts)."""
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def date_pose(equipement) -> tuple[date | None, str | None]:
    """(date, statut) : la date exacte si elle est connue, sinon le 1er juillet de l'année."""
    exacte = _champ(equipement, "date_pose")
    if exacte:
        return exacte, "calcule"
    annee = _champ(equipement, "annee_pose")
    if annee:
        return date(annee, 7, 1), "suppose"
    return None, None


def age_ans(equipement, aujourd_hui: date) -> tuple[int | None, str | None]:
    """Âge en années révolues, et le statut de la date dont il part."""
    pose, statut = date_pose(equipement)
    if pose is None:
        return None, None
    age = aujourd_hui.year - pose.year - ((aujourd_hui.month, aujourd_hui.day) < (pose.month, pose.day))
    return max(age, 0), statut


def garanties_maison(equipements, travaux, aujourd_hui: date) -> list[dict]:
    """Toutes les garanties connues de la maison, triées par date de fin (la plus proche d'abord).

    Un équipement hors service n'y figure plus : sa garantie ne protège plus rien dans la
    maison. Des travaux sans date de réception n'ouvrent aucune garantie.
    """
    entrees = []
    for t in travaux:
        reception = _champ(t, "date_reception")
        if not reception:
            continue
        for g in fin_garanties_chantier(reception):
            entrees.append({
                "provenance": "travaux",
                "source_id": _champ(t, "id"),
                "code": g["code"],
                "libelle": f"{g['libelle']} — {_champ(t, 'nature')}",
                "debut": reception,
                "fin": g["fin"],
                "statut": statut_garantie(g["fin"], aujourd_hui),
                "donnees": "calcule",
                "mention": MENTION_VERIFICATION,
            })
    for e in equipements:
        fin = _champ(e, "garantie_fabricant_fin")
        if not fin or _champ(e, "en_service") is False:
            continue
        nom = " ".join(x for x in (_champ(e, "marque"), _champ(e, "modele")) if x) or _champ(e, "type")
        entrees.append({
            "provenance": "equipement",
            "source_id": _champ(e, "id"),
            "code": "fabricant",
            "libelle": f"Garantie fabricant — {nom}",
            "debut": date_pose(e)[0],
            "fin": fin,
            "statut": statut_garantie(fin, aujourd_hui),
            # La date de fin est saisie telle quelle par le foyer, rien n'est déduit.
            "donnees": "declare",
            "mention": None,
        })
    return sorted(entrees, key=lambda g: g["fin"])
