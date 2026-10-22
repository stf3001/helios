"""Relevé mensuel des mises en relation d'un partenaire (mises en relation, lot 4). Pur.

UN RELEVÉ N'EST PAS UNE FACTURE : la société Hélios n'existe pas encore. Pas de numéro, pas de
mentions légales de facture ; la TVA et le TTC sont indicatifs. La facturation viendra se
brancher sur l'instantané d'un relevé CLOS, qui ne bouge plus.

- Période : mois civil À L'HEURE DE PARIS, selon la date de TRANSMISSION (`consent_client_at`).
- Lignes : les mises en relation `travaux` à prix fixe (`prix_ht` renseigné) ; jamais le nom, le
  téléphone ni l'e-mail du foyer — le code postal seulement.
- Total : les seules lignes facturables. Une contestation en attente est listée à part et
  EXCLUE tant qu'elle n'est pas tranchée ; acceptée, exclue ; refusée, la ligne compte.
  Un retrait de consentement par le foyer ne change rien : le prix est dû à la transmission.
"""
from datetime import date, datetime, time, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.core.config import settings
from app.services.creneaux import fuseau_paris, heure_de_paris

ETATS = {
    "facturable": "Facturable",
    "contestation_en_cours": "Contestation en cours",
    "contestation_acceptee": "Contestation acceptée",
}
JOUR_CLOTURE = 8  # au plus tôt le 8 du mois suivant : après le délai de contestation des leads du 31


class MoisInvalide(ValueError):
    pass


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _eur(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def lire_mois(mois: str) -> tuple[int, int]:
    try:
        annee, m = (int(x) for x in mois.split("-"))
        if len(mois) != 7 or not 1 <= m <= 12:
            raise ValueError
    except ValueError:
        raise MoisInvalide(f"Mois illisible : « {mois} » (attendu AAAA-MM).")
    return annee, m


def mois_suivant(annee: int, m: int) -> tuple[int, int]:
    return (annee + 1, 1) if m == 12 else (annee, m + 1)


def mois_de(moment: datetime) -> str:
    """Le mois d'un instant, à l'horloge de Paris."""
    return heure_de_paris(moment).strftime("%Y-%m")


def bornes(mois: str) -> tuple[datetime, datetime]:
    """[début, fin[ du mois à Paris, en UTC — pour filtrer en base sans rater une heure."""
    annee, m = lire_mois(mois)
    a2, m2 = mois_suivant(annee, m)
    def minuit(a, mm):
        j = date(a, mm, 1)
        return datetime.combine(j, time(0), tzinfo=fuseau_paris(j)).astimezone(timezone.utc)
    return minuit(annee, m), minuit(a2, m2)


def cloture_possible_le(mois: str) -> date:
    a2, m2 = mois_suivant(*lire_mois(mois))
    return date(a2, m2, JOUR_CLOTURE)


def releve(partenaire, leads, contestations, mois: str, codes_postaux: dict | None = None) -> dict:
    """`contestations` : celles des leads (une au plus par lead) ; `codes_postaux` : lead_id → code postal."""
    codes_postaux = codes_postaux or {}
    par_lead = {_champ(c, "lead_id"): c for c in contestations}
    pid = _champ(partenaire, "id")
    lignes = []
    for l in leads:
        if (_champ(l, "partner_id") != pid or _champ(l, "type") != "travaux" or _champ(l, "prix_ht") is None
                or mois_de(_champ(l, "consent_client_at")) != mois):
            continue
        c = par_lead.get(_champ(l, "id"))
        statut_c = _champ(c, "statut") if c is not None else None
        if statut_c == "en_attente":
            etat = "contestation_en_cours"
        elif statut_c == "acceptee" or not _champ(l, "facturable"):
            etat = "contestation_acceptee"
        else:
            etat = "facturable"
        transmis = heure_de_paris(_champ(l, "consent_client_at"))
        lignes.append({
            "lead_id": str(_champ(l, "id")), "date": transmis.date().isoformat(), "heure": transmis.strftime("%H:%M"),
            "metier": _champ(l, "metier"), "code_postal": codes_postaux.get(_champ(l, "id")),
            "prix_ht": float(_eur(_champ(l, "prix_ht"))), "etat": etat, "contestation_refusee": statut_c == "refusee",
        })
    lignes.sort(key=lambda x: (x["date"], x["heure"], x["lead_id"]))
    total = sum((_eur(x["prix_ht"]) for x in lignes if x["etat"] == "facturable"), Decimal("0"))
    tva = _eur(total * Decimal(str(settings.mer_tva_taux)))
    return {
        "mois": mois,
        "partenaire": {"id": str(pid), "raison_sociale": _champ(partenaire, "raison_sociale"),
                       "siret": _champ(partenaire, "siret")},
        "lignes": lignes,
        "nb_lignes": len(lignes),
        "nb_facturables": sum(x["etat"] == "facturable" for x in lignes),
        "nb_contestees": sum(x["etat"] != "facturable" or x["contestation_refusee"] for x in lignes),
        "en_attente": [x for x in lignes if x["etat"] == "contestation_en_cours"],
        "total_ht": float(total),
        "tva_taux": settings.mer_tva_taux,
        "tva": float(tva),
        "ttc": float(total + tva),
    }
