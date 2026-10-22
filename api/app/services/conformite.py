"""Un partenaire est-il en règle ? Justificatifs et charte (mises en relation, lot 3). Pur.

C'est le SEUL endroit qui le décide : `propositions.eligible` reçoit sa réponse. Un partenaire
qui n'est pas en règle sort des propositions, mais garde l'accès à ses demandes passées.

- Kbis : déposé et non refusé. Il doit avoir moins de 3 mois AU DÉPÔT (`kbis_recent`), pas après.
- Décennale : date de fin connue et non dépassée.
- RGE : seulement si le partenaire se déclare RGE ; date de fin non dépassée.
- Charte : la version signée est la version en vigueur (la plus récente de `chartes`). Tant
  qu'aucune n'est en vigueur, personne n'est en règle.

Un justificatif compte tant qu'il est déposé, non refusé et non expiré : pas d'étape « à
vérifier » qui bloquerait les propositions en attendant l'administration.
"""
from datetime import date, timedelta

from app.core.config import settings

TYPES = ("kbis", "decennale", "rge")
LIBELLES = {"kbis": "Extrait Kbis", "decennale": "Attestation d'assurance décennale", "rge": "Qualification RGE"}
AVEC_DATE_FIN = ("decennale", "rge")
ECHEANCE_PROCHE_JOURS = 30


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def kbis_recent(date_delivrance: date | None, aujourd_hui: date) -> bool:
    """Moins de `mer_kbis_max_mois` mois (compté en jours : 30 par mois)."""
    return (date_delivrance is not None and date_delivrance <= aujourd_hui
            and aujourd_hui - date_delivrance <= timedelta(days=30 * settings.mer_kbis_max_mois))


def types_requis(rge_declare: bool) -> tuple[str, ...]:
    return TYPES if rge_declare else ("kbis", "decennale")


def etat_justificatifs(rge_declare: bool, documents, aujourd_hui: date) -> dict:
    """Pour chaque type requis, le justificatif retenu (le plus récent non refusé) et son état :
    `manquant`, `expire`, `bientot` (fin dans 30 jours ou moins) ou `valide`."""
    etats = {}
    for t in types_requis(rge_declare):
        candidats = [d for d in documents if _champ(d, "type") == t and _champ(d, "statut") != "refuse"]
        doc = max(candidats, key=lambda d: (_champ(d, "created_at") is not None, _champ(d, "created_at")),
                  default=None)
        fin = _champ(doc, "date_fin") if doc is not None else None
        if doc is None or (t in AVEC_DATE_FIN and fin is None):
            etat = "manquant"
        elif t in AVEC_DATE_FIN and fin < aujourd_hui:
            etat = "expire"
        elif t in AVEC_DATE_FIN and (fin - aujourd_hui).days <= ECHEANCE_PROCHE_JOURS:
            etat = "bientot"
        else:
            etat = "valide"
        etats[t] = {"etat": etat, "date_fin": fin, "document_id": _champ(doc, "id") if doc is not None else None}
    return etats


def charte_a_jour(version_signee: str | None, version_en_vigueur: str | None) -> bool:
    return version_en_vigueur is not None and version_signee == version_en_vigueur


def en_regle(rge_declare: bool, documents, version_signee: str | None, version_en_vigueur: str | None,
             aujourd_hui: date) -> bool:
    etats = etat_justificatifs(rge_declare, documents, aujourd_hui)
    return (charte_a_jour(version_signee, version_en_vigueur)
            and all(e["etat"] in ("valide", "bientot") for e in etats.values()))


def alertes(rge_declare: bool, documents, version_signee: str | None, version_en_vigueur: str | None,
            aujourd_hui: date) -> list[str]:
    """Les phrases de la bannière de l'espace partenaire, des plus bloquantes aux autres."""
    out = []
    if version_en_vigueur is None:
        out.append("La charte partenaire est en cours de relecture : vous ne recevez pas encore de demandes.")
    elif version_signee != version_en_vigueur:
        out.append(f"Signez la charte {version_en_vigueur} pour recevoir de nouvelles demandes.")
    for t, e in etat_justificatifs(rge_declare, documents, aujourd_hui).items():
        if e["etat"] == "manquant":
            out.append(f"{LIBELLES[t]} à déposer : sans lui, vous ne recevez plus de nouvelles demandes.")
        elif e["etat"] == "expire":
            out.append(f"{LIBELLES[t]} expiré le {e['date_fin']:%d/%m/%Y} : déposez le nouveau pour recevoir "
                       "de nouvelles demandes.")
        elif e["etat"] == "bientot":
            out.append(f"{LIBELLES[t]} arrive à échéance le {e['date_fin']:%d/%m/%Y}.")
    return out
