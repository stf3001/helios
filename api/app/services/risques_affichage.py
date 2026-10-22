"""Ce que la section « Les risques de ma commune » et le chat disent des risques (phase 2). Pur.

Une ligne par risque PRÉSENT, sans pourcentage ni niveau inventé, avec le lien vers sa question
de `kb/risques_maison.md` (les intitulés sont recopiés à l'identique : la page de la fiche se
retrouve par son slug). Un risque sans question propre renvoie à la question générale.
"""
from app.services.georisques import RISQUES

LIBELLES = {
    "inondation": "Inondation",
    "argiles": "Retrait-gonflement des argiles",
    "feux_de_foret": "Feux de forêt",
    "mouvement_de_terrain": "Mouvements de terrain",
    "seisme": "Séisme",
    "radon": "Radon",
    "industriel": "Risques technologiques (industrie, transport de matières dangereuses, sols pollués…)",
    "autre": "Autres risques naturels",
}
Q_GENERALE = "Comment savoir à quels risques ma commune est exposée ?"
QUESTIONS = {
    "inondation": "Vigilance orange pour pluie-inondation : que faire pour la maison ?",
    "argiles": "Ma commune est concernée par le retrait-gonflement des argiles : que faire pour ma maison ?",
    "feux_de_foret": "Ma commune est exposée aux feux de forêt : qu'est-ce que je dois faire ?",
    "radon": "Ma commune a un potentiel radon : qu'est-ce que ça change ?",
}
Q_FISSURE = "Une fissure apparaît sur ma maison : quand faut-il s'inquiéter ?"
MENTION = ("À l'échelle de votre commune : ces informations disent ce qui existe autour de vous, pas ce qui "
           "touche votre parcelle. Pour votre adresse, c'est l'état des risques qui fait foi.")
CHAT_MAX = 200


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def section(ligne, maison, verifications: list[dict]) -> dict:
    """La section, prête à afficher. `verifications` : celles du moteur d'entretien (« ne sais pas »)."""
    risques = [r for r in RISQUES if r in (_champ(ligne, "risques") or [])]
    deb = None
    if "feux_de_foret" in risques and _champ(maison, "zone_old") == "ne_sais_pas":
        # L'invitation EXISTANTE du calendrier d'entretien remonte ici, telle quelle.
        deb = next((v for v in verifications if v.get("champ") == "zone_old"), None)
    collecte = _champ(ligne, "collecte_le")
    return {
        "commune": _champ(maison, "commune") or _champ(ligne, "commune"),
        "code_insee": _champ(ligne, "code_insee"),
        "risques": [{"code": r, "libelle": LIBELLES[r], "question": QUESTIONS.get(r, Q_GENERALE)} for r in risques],
        "catnat_30_ans": _champ(ligne, "catnat_30_ans"),
        "radon_classe": _champ(ligne, "radon_classe"),
        "zone_sismique": _champ(ligne, "zone_sismique"),
        "ppr": _champ(ligne, "ppr"),
        "url_rapport": _champ(ligne, "url_rapport"),
        "collecte_le": collecte.isoformat() if hasattr(collecte, "isoformat") else collecte,
        "mention": MENTION,
        "question_generale": Q_GENERALE,
        "debroussaillement": deb,
        "fissure": {"question": Q_FISSURE} if "argiles" in risques else None,
    }


def pour_le_chat(ligne) -> dict | None:
    """Liste courte des risques présents, statut `observe` (source publique), < 200 caractères."""
    risques = [r for r in RISQUES if r in (_champ(ligne, "risques") or [])] if ligne is not None else []
    if not risques:
        return None
    texte = ", ".join(r for r in risques)
    if len(texte) > CHAT_MAX:
        texte = texte[:CHAT_MAX - 1].rsplit(",", 1)[0]
    return {"liste": texte, "statut": "observe", "echelle": "commune"}
