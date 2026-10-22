"""La note d'un locataire pour son propriétaire (carnet, lot 8) — fonction pure.

Un texte sobre, à COPIER : rien n'est envoyé. Il reprend les tâches à la charge du
propriétaire dépassées ou proches, et les équipements de plus de quinze ans ; sans chiffre,
sans coût, sans nom d'entreprise. Les phrases sont recopiées MOT POUR MOT de
`kb/locataire_entretien.md`, section « Pour la note au propriétaire »
(`tests/test_parcours.py` le vérifie) : changer la fiche, puis recopier.
"""
from datetime import date

from app.services.garanties import age_ans
from app.services.pdf_dossier import _TYPES as LIBELLES_TYPES

AGE_SIGNALE = 15  # ans révolus : 15 ans et quelques mois, c'est déjà « plus de quinze ans »

PHRASES = {
    "ouverture": "Bonjour, je vous écris au sujet de l'entretien du logement que je loue.",
    "taches": "D'après le calendrier d'entretien que je tiens, ces opérations à votre charge sont "
              "dépassées ou arrivent bientôt :",
    "retard": "échéance dépassée",
    "bientot": "à prévoir prochainement",
    "equipements": "Ces équipements ont plus de quinze ans ; je vous les signale pour que vous puissiez anticiper :",
    "rien": "Je n'ai rien de particulier à signaler pour l'instant : tout est à jour d'après mon calendrier.",
    "bail": "Je m'appuie sur la répartition habituelle des charges, sauf clause contraire de notre bail.",
    "cloture": "Je reste disponible pour en parler. Bien cordialement.",
}


def _nom(e) -> str:
    return LIBELLES_TYPES.get(e.type, e.type)


def note(echeances: list[dict], equipements, aujourd_hui: date) -> str:
    """`echeances` : celles du moteur, déjà marquées ; seules celles qui ne reviennent pas au
    locataire PARCE QU'elles sont au propriétaire sont reprises (pas la copropriété)."""
    noms = {e.id: _nom(e) for e in equipements}
    taches = []
    for e in echeances:
        if e["pour_moi"] or e["responsable"] != "proprietaire" or e["statut"] not in ("en_retard", "ce_mois", "bientot"):
            continue
        objet = f" ({noms[e['equipement_id']]})" if e["equipement_id"] in noms else ""
        etat = PHRASES["retard"] if e["statut"] == "en_retard" else PHRASES["bientot"]
        taches.append(f"- {e['libelle']}{objet} : {etat}")
    anciens = [f"- {_nom(e)}" for e in equipements
               if e.en_service and (age_ans(e, aujourd_hui)[0] or 0) >= AGE_SIGNALE]

    blocs = [PHRASES["ouverture"]]
    if taches:
        blocs.append("\n".join([PHRASES["taches"], *taches]))
    if anciens:
        blocs.append("\n".join([PHRASES["equipements"], *anciens]))
    if not taches and not anciens:
        blocs.append(PHRASES["rien"])
    blocs += [PHRASES["bail"], PHRASES["cloture"]]
    return "\n\n".join(blocs)
