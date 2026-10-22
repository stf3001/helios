"""Un parcours par statut et par type de logement (carnet, lot 8) — fonctions pures.

La fiche dit `statut` (propriétaire, locataire, en cours d'achat) et `type_logement` ; ce
module en tire ce que l'espace montre. Les échéances elles-mêmes sont marquées par le moteur
d'entretien (`pour_moi`, `mention`) : ici, seulement ce qui change d'ÉCRAN.

- Propriétaire (ou statut inconnu) : tout, comme avant le lot 8.
- Locataire : ni garanties de chantier, ni travaux, ni projets lourds ; la note au
  propriétaire (`note_proprietaire.py`).
- Acheteur : « Avant d'acheter » remplace le bloc « À faire ». Au passage à propriétaire, la
  liste est archivée au journal.

Les libellés de la liste sont recopiés MOT POUR MOT de `kb/achat_logement.md`, section
« Pour le carnet » (`tests/test_parcours.py` le vérifie) : changer la fiche, puis recopier.
"""
from datetime import date

# (id, libellé), dans l'ordre de la fiche.
ITEMS_AVANT_ACHAT: tuple[tuple[str, str], ...] = (
    ("dpe", "Le diagnostic de performance énergétique (DPE)"),
    ("diagnostics", "Le dossier de diagnostic technique, et l'audit énergétique s'il est exigé"),
    ("cil", "Le carnet d'information du logement, s'il a été construit ou rénové énergétiquement depuis 2023"),
    ("entretien", "Les attestations d'entretien de la chaudière, de la pompe à chaleur ou du poêle, "
                  "et de ramonage, des deux dernières années"),
    ("debroussaillement", "L'attestation du vendeur sur le respect de l'obligation de débroussaillement, "
                          "si le terrain y est soumis"),
    ("spanc", "Le rapport du SPANC de moins de 3 ans, si le logement n'est pas raccordé au tout-à-l'égout"),
    ("travaux", "Les factures et garanties des travaux récents, notamment l'attestation d'assurance décennale"),
)
# Pas posées à un appartement (décision du 20/10/2026, comme les tâches d'entretien).
_DE_MAISON = ("debroussaillement", "spanc")
# Le type de document proposé au dépôt d'une pièce reçue (types existants de `house_documents`).
TYPE_DOCUMENT = {"dpe": "dpe"}
# La question de `kb/achat_logement.md` vers laquelle renvoie « En savoir plus ».
FICHE_ACHAT = "J'achète un logement : quels papiers demander au vendeur sur son énergie et son entretien ?"
TITRE_ARCHIVE = "Avant d'acheter : documents demandés au vendeur"


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def parcours(maison) -> dict:
    statut = _champ(maison, "statut")
    locataire = statut == "locataire"
    return {
        "profil": {"locataire": "locataire", "en_achat": "acheteur"}.get(statut, "proprietaire"),
        "voit_travaux": not locataire,
        # Aucun projet n'existe encore : le lot 9 lira ce drapeau pour masquer les projets lourds.
        "voit_projets_lourds": not locataire,
        "avant_d_acheter": statut == "en_achat",
        "note_proprietaire": locataire,
    }


def garanties_visibles(garanties: list[dict], maison) -> list[dict]:
    """Un locataire ne décide pas des travaux : leurs garanties de chantier ne lui sont pas
    montrées. Celles des appareils (garantie fabricant), si."""
    if _champ(maison, "statut") != "locataire":
        return garanties
    return [g for g in garanties if g.get("provenance") != "travaux"]


def items_applicables(maison) -> list[tuple[str, str]]:
    appartement = _champ(maison, "type_logement") == "appartement"
    sortie = []
    for item_id, libelle in ITEMS_AVANT_ACHAT:
        if appartement and item_id in _DE_MAISON:
            continue
        if item_id == "debroussaillement" and _champ(maison, "zone_old") == "non":
            continue
        sortie.append((item_id, libelle))
    return sortie


def avant_achat(maison) -> list[dict]:
    """Les lignes à cocher, avec ce que le foyer a déjà coché ou joint."""
    etat = _champ(maison, "avant_achat") or {}
    return [{
        "id": item_id, "libelle": libelle,
        "coche": bool((etat.get(item_id) or {}).get("coche")),
        "document_id": (etat.get(item_id) or {}).get("document_id"),
        "type_document": TYPE_DOCUMENT.get(item_id, "autre"),
    } for item_id, libelle in items_applicables(maison)]


def archive(lignes: list[dict], noms_documents: dict, aujourd_hui: date) -> dict:
    """L'entrée de journal écrite au passage à propriétaire : la liste telle qu'elle était."""
    texte = []
    for l in lignes:
        doc = noms_documents.get(str(l["document_id"])) if l["document_id"] else None
        texte.append(f"{'Reçu' if l['coche'] else 'Non reçu'} — {l['libelle']}"
                     + (f" (document joint : {doc})" if doc else ""))
    return {"date": aujourd_hui, "type": "autre", "titre": TITRE_ARCHIVE, "note": "\n".join(texte)}
