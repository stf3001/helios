"""Mises en relation à prix fixe (série 4, lot 1) : qui est éligible, et le tirage au sort. Pur.

Le foyer choisit parmi au plus `mer_nb_propositions` partenaires, TIRÉS AU SORT parmi les
éligibles et présentés dans un ordre aléatoire : jamais triés par note, ancienneté ou nombre
de leads. Hélios est payé le même prix fixe quel que soit le partenaire choisi : il n'a
aucune raison d'en pousser un.
"""
import random

from app.core.config import settings
from app.services import regions

# Les métiers d'une mise en relation `travaux` : ceux de l'annuaire, sauf le courtage (`energie`).
METIERS_TRAVAUX = tuple(m for m in regions.METIERS if m != "courtage")
# Un lead « actif » occupe une place : il n'est ni perdu, ni signé.
STATUTS_ACTIFS = ("nouveau", "transmis", "contacte", "devis")
STATUTS_FOYER = ("proprietaire", "en_achat")
NB_AVIS_MIN_NOTE = 3  # la note moyenne n'est montrée qu'à partir de 3 avis

# Recopié tel quel de la décision de Stéphane (22/10/2026).
CONSENTEMENT = ("J'accepte que ma demande et les informations de mon projet que j'ai choisies soient "
                "transmises à {raison_sociale}, qui pourra me contacter au sujet de ce projet.")


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def voit_les_demos(email: str | None) -> bool:
    return email is not None and email.lower() in settings.mer_comptes_demo


def eligible(partenaire, departement: str | None, metier: str, voit_demo: bool = False) -> bool:
    """Un partenaire de démonstration ne l'est que pour un compte de démonstration (point 60)."""
    if _champ(partenaire, "demo") and not voit_demo:
        return False
    return (_champ(partenaire, "statut") == "actif"
            and _champ(partenaire, "charte_signee_at") is not None
            and departement is not None and departement in (_champ(partenaire, "zones") or [])
            and metier in (_champ(partenaire, "metiers") or []))


def tirer(eligibles: list, n: int, rng: random.Random | None = None) -> list:
    """Au plus `n` partenaires au hasard, dans un ordre lui aussi au hasard (`sample` fait les deux)."""
    return (rng or random).sample(list(eligibles), min(n, len(eligibles)))


def proposition(partenaire, nb_avis: int) -> dict:
    """Ce que voit le foyer : ni SIRET ni e-mail ; la note seulement à partir de 3 avis."""
    note = _champ(partenaire, "note_moyenne") if nb_avis >= NB_AVIS_MIN_NOTE else None
    return {
        "id": _champ(partenaire, "id"), "raison_sociale": _champ(partenaire, "raison_sociale"),
        "rge": bool(_champ(partenaire, "rge")), "note_moyenne": note, "nb_avis": nb_avis,
        "lien_interet": _champ(partenaire, "lien_interet"),
        "consentement": CONSENTEMENT.format(raison_sociale=_champ(partenaire, "raison_sociale")),
    }


def refus_creation(statut_foyer: str | None, metier: str | None, partenaire, departement: str | None,
                   leads_actifs: list, voit_demo: bool = False) -> str | None:
    """La raison de refuser une mise en relation `travaux`, ou None. `leads_actifs` : ceux du
    foyer qui ne sont ni perdus ni signés."""
    if statut_foyer == "locataire":
        return "Ces travaux se décident avec votre propriétaire."
    if statut_foyer not in STATUTS_FOYER:
        return "Indiquez dans votre fiche si vous êtes propriétaire ou en cours d'achat."
    if metier not in METIERS_TRAVAUX:
        return "Choisissez le métier concerné."
    if not eligible(partenaire, departement, metier, voit_demo):
        return "Ce partenaire n'est pas proposé pour votre projet."
    meme_metier = [l for l in leads_actifs if _champ(l, "metier") == metier]
    if any(_champ(l, "partner_id") == _champ(partenaire, "id") for l in meme_metier):
        return "Une demande à ce partenaire pour ce métier est déjà en cours."
    if len(meme_metier) >= settings.mer_nb_propositions:
        return f"Vous avez déjà {settings.mer_nb_propositions} demandes en cours pour ce métier."
    return None
