"""Le bloc « À faire ce mois-ci » et le journal fusionné — fonctions pures (carnet, lot 4).

Le bloc ne calcule rien : il CHOISIT parmi les échéances du moteur d'entretien
(`services/entretien.py`) et les garanties (`services/garanties.py`). Règle de contenu
(décision de Stéphane) : tâches en retard et du mois, puis jusqu'à 3 « bientôt », puis les
garanties qui expirent bientôt ; au plus 6 lignes, le reste est derrière « Tout voir ».

Lot 8 : seules les échéances `pour_moi` y entrent — une tâche à la charge du propriétaire
d'un locataire, ou une chaudière assurée par la copropriété, reste lisible dans le
calendrier mais ne relance pas le foyer.
"""
from datetime import date

MAX_LIGNES = 6
MAX_BIENTOT = 3


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def a_faire(echeances: list[dict], garanties: list[dict], aujourd_hui: date, table_vide: bool = False) -> dict:
    """`echeances` arrive déjà trié par le moteur ; on garde son ordre."""
    echeances = [e for e in echeances if e.get("pour_moi", True)]
    urgentes = [e for e in echeances if e["statut"] in ("en_retard", "ce_mois")]
    bientot = [e for e in echeances if e["statut"] == "bientot"][:MAX_BIENTOT]
    lignes = [{"kind": "tache", **e} for e in urgentes + bientot]
    lignes += [{"kind": "garantie", **g} for g in garanties if g["statut"] == "bientot"]
    total = len(lignes)
    lignes = lignes[:MAX_LIGNES]

    # « Rien à faire ce mois-ci. Prochaine échéance : … » — la plus proche de celles qui restent.
    prochaine = None
    if not lignes:
        datees = [e for e in echeances if e["echeance"] and e["statut"] == "plus_tard"]
        if datees:
            e = min(datees, key=lambda x: x["echeance"])
            prochaine = {"libelle": e["libelle"], "echeance": e["echeance"], "equipement_id": e["equipement_id"]}
    return {
        "lignes": lignes,
        "masquees": total - len(lignes),
        "table_vide": table_vide,
        "rien_d_urgent": not lignes,
        "prochaine": prochaine,
    }


def derniers_faits(entrees) -> dict:
    """{(tache_id, equipement_id) : date la plus récente} — ce que le moteur prend pour référence."""
    faits: dict = {}
    for e in entrees:
        tache = _champ(e, "tache_id")
        if not tache:
            continue
        cle = (tache, _champ(e, "equipement_id"))
        if cle not in faits or _champ(e, "date") > faits[cle]:
            faits[cle] = _champ(e, "date")
    return faits


def journal_fusionne(entrees, travaux, equipement_id=None, travaux_de_l_equipement=frozenset()) -> list[dict]:
    """Entrées du journal et travaux du lot 1, du plus récent au plus ancien.

    Un chantier sans date de réception se place à sa date de saisie, marqué comme tel.
    Filtre par équipement : ses entrées, et les chantiers auxquels il est rattaché.
    """
    lignes = []
    for e in entrees:
        if equipement_id is not None and _champ(e, "equipement_id") != equipement_id:
            continue
        lignes.append({
            "source": "journal", "id": _champ(e, "id"), "date": _champ(e, "date"), "type": _champ(e, "type"),
            "titre": _champ(e, "titre"), "equipement_id": _champ(e, "equipement_id"),
            "piece_id": _champ(e, "piece_id"), "tache_id": _champ(e, "tache_id"),
            "intervenant": _champ(e, "intervenant"), "cout_eur": _champ(e, "cout_eur"),
            "document_id": _champ(e, "document_id"), "note": _champ(e, "note"),
            "justifie": _champ(e, "document_id") is not None, "date_reception_connue": True,
        })
    for t in travaux:
        if equipement_id is not None and _champ(t, "id") not in travaux_de_l_equipement:
            continue
        reception = _champ(t, "date_reception")
        cree = _champ(t, "created_at")
        lignes.append({
            "source": "travaux", "id": _champ(t, "id"),
            "date": reception or (cree.date() if hasattr(cree, "date") else cree),
            "type": "travaux", "titre": _champ(t, "nature"), "intervenant": _champ(t, "entreprise"),
            "cout_eur": _champ(t, "montant_ttc"), "note": _champ(t, "note"),
            "document_id": _champ(t, "facture_document_id") or _champ(t, "attestation_assurance_document_id"),
            "justifie": bool(_champ(t, "facture_document_id") or _champ(t, "attestation_assurance_document_id")),
            "date_reception_connue": reception is not None,
        })
    return sorted(lignes, key=lambda l: (l["date"], l["source"] == "journal"), reverse=True)
