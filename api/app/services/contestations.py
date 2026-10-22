"""Contester une mise en relation (mises en relation, lot 3). Pur.

Dans les `mer_delai_contestation_jours` (7 jours calendaires) qui suivent la transmission, un
partenaire peut contester une demande `travaux` pour un motif de la liste, avec un commentaire
obligatoire. L'administration accepte ou refuse : acceptée, la demande n'est plus facturable
(`leads.facturable = false`, `prix_ht` gardé). Une seule contestation par demande.
"""
from datetime import date, datetime, timedelta

from app.core.config import settings

MOTIFS = {
    "coordonnees_fausses": "Coordonnées fausses",
    "hors_zone_ou_metier": "Hors de ma zone ou de mes métiers",
    "doublon": "Doublon : même foyer, même métier, déjà reçu dans les 12 mois (par Hélios ou en direct)",
    "injoignable": "Foyer injoignable après trois essais dans ses créneaux",
}
NB_ESSAIS = 3
DOUBLON_MOIS = 12


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def fin_delai(transmis_le: datetime) -> datetime:
    return transmis_le + timedelta(days=settings.mer_delai_contestation_jours)


def dans_le_delai(lead, maintenant: datetime) -> bool:
    return maintenant <= fin_delai(_champ(lead, "consent_client_at"))


def peut_contester(lead, maintenant: datetime, contestations: list) -> bool:
    """Ce qui fait apparaître le bouton : demande `travaux`, dans le délai, jamais contestée."""
    return _champ(lead, "type") == "travaux" and dans_le_delai(lead, maintenant) and not contestations


def refus(lead, maintenant: datetime, contestations: list, motif: str, commentaire: str | None,
          essais: list[date] | None) -> str | None:
    """La raison de refuser la contestation, ou None."""
    if _champ(lead, "type") != "travaux":
        return "Seule une mise en relation de travaux se conteste."
    if contestations:
        return "Cette demande a déjà été contestée."
    if not dans_le_delai(lead, maintenant):
        return f"Le délai de {settings.mer_delai_contestation_jours} jours pour contester est dépassé."
    if motif not in MOTIFS:
        return "Motif inconnu."
    if not (commentaire or "").strip():
        return "Un commentaire est obligatoire."
    if motif == "injoignable":
        jours = sorted(essais or [])  # deux essais le même jour, à deux créneaux, comptent pour deux
        transmis = _champ(lead, "consent_client_at").date()
        if len(jours) < NB_ESSAIS:
            return f"Indiquez les dates de vos {NB_ESSAIS} essais."
        if any(j < transmis or j > maintenant.date() for j in jours):
            return "Les essais doivent dater d'après la transmission, et pas du futur."
    return None
