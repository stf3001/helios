"""Les rendez-vous vus par l'équipe (back-office) — fonctions pures.

« À venir » garde un appel commencé mais pas fini : on peut encore le passer. « Passés » ne
remonte qu'à 60 jours. Les heures sortent à l'horloge de Paris (`creneaux.heure_de_paris`),
été comme hiver.
"""
from datetime import datetime, timedelta

from app.services.creneaux import heure_de_paris

JOURS_PASSES = 60


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _fin(rdv) -> datetime:
    return _champ(rdv, "debut") + timedelta(minutes=_champ(rdv, "duree_min") or 30)


def filtrer(rdvs, periode: str, maintenant: datetime) -> list:
    """`a_venir` : du plus proche au plus lointain ; `passes` : du plus récent au plus ancien."""
    if periode == "passes":
        plancher = maintenant - timedelta(days=JOURS_PASSES)
        retenus = [r for r in rdvs if _fin(r) <= maintenant and _champ(r, "debut") >= plancher]
        return sorted(retenus, key=lambda r: _champ(r, "debut"), reverse=True)
    retenus = [r for r in rdvs if _fin(r) > maintenant]
    return sorted(retenus, key=lambda r: _champ(r, "debut"))


def resume_a_venir(rdvs, maintenant: datetime) -> dict:
    """La tuile du tableau de bord : combien, et le prochain (les annulés ne comptent pas)."""
    a_venir = [r for r in filtrer(rdvs, "a_venir", maintenant) if _champ(r, "statut") != "annule"]
    prochain = a_venir[0] if a_venir else None
    return {
        "a_venir": len(a_venir),
        "prochain": heure_de_paris(_champ(prochain, "debut")).isoformat() if prochain else None,
        # Passés mais encore « réservé » : personne n'a dit s'il avait eu lieu.
        "a_qualifier": sum(1 for r in filtrer(rdvs, "passes", maintenant) if _champ(r, "statut") == "reserve"),
    }
