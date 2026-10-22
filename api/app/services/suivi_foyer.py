"""Suivi d'une mise en relation côté foyer, écarts et indicateurs (mises en relation, lot 5). Pur.

- Le foyer n'est jamais laissé sans recours : 5 jours ouvrés après la transmission, si le
  partenaire n'a déclaré aucun contact, on lui demande « L'entreprise vous a-t-elle contacté ? ».
- Ses déclarations (devis reçu, travaux signés, projet abandonné) vivent À CÔTÉ du statut tenu par
  le partenaire : c'est ce qui permet de voir les écarts. Rien ici ne touche au prix.
- Les indicateurs disent chacun leur source : déclaré partenaire, déclaré foyer, ou calculé.
"""
from datetime import date, datetime, timedelta
from statistics import mean

from app.core.config import settings
from app.services.creneaux import heure_de_paris
from app.services.releves import mois_de

# Jours fériés de métropole : code du travail, art. L. 3133-1 (1er janvier, lundi de Pâques,
# 1er mai, 8 mai, Ascension, lundi de Pentecôte, 14 juillet, 15 août, 1er novembre, 11 novembre,
# 25 décembre). Les fêtes de Pâques sont calculées ; l'Alsace-Moselle (Vendredi saint, 26 décembre)
# n'est pas comptée.
FERIES_FIXES = ((1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25))

DECLARATIONS = {"devis_recu": "Devis reçu", "travaux_signes": "Travaux signés", "projet_abandonne": "Projet abandonné"}
STATUTS_CONTACT_PARTENAIRE = ("contacte", "devis", "signe")


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def paques(annee: int) -> date:
    """Dimanche de Pâques (calendrier grégorien, algorithme de Meeus / Jones / Butcher)."""
    a, b, c = annee % 19, annee // 100, annee % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois = (h + l - 7 * m + 114) // 31
    jour = (h + l - 7 * m + 114) % 31 + 1
    return date(annee, mois, jour)


def feries(annee: int) -> set[date]:
    p = paques(annee)
    return {date(annee, m, j) for m, j in FERIES_FIXES} | {
        p + timedelta(days=1),   # lundi de Pâques
        p + timedelta(days=39),  # Ascension
        p + timedelta(days=50),  # lundi de Pentecôte
    }


def jour_ouvre(d: date) -> bool:
    return d.weekday() < 5 and d not in feries(d.year)


def jours_ouvres_depuis(depart: date, aujourd_hui: date) -> int:
    """Jours ouvrés écoulés APRÈS `depart`, jusqu'à `aujourd_hui` inclus."""
    n, d = 0, depart + timedelta(days=1)
    while d <= aujourd_hui:
        n += jour_ouvre(d)
        d += timedelta(days=1)
    return n


def _jour_paris(moment: datetime) -> date:
    return heure_de_paris(moment).date()


def contact_declare_par_partenaire(lead) -> bool:
    return _champ(lead, "contacte_le") is not None or _champ(lead, "statut") in STATUTS_CONTACT_PARTENAIRE


def question_contact_due(lead, aujourd_hui: date) -> bool:
    """« L'entreprise vous a-t-elle contacté ? » : délai écoulé, aucun contact déclaré, pas de réponse."""
    return (_champ(lead, "type") == "travaux"
            and _champ(lead, "consent_retire_at") is None
            and _champ(lead, "statut") == "transmis"
            and not contact_declare_par_partenaire(lead)
            and _champ(lead, "contact_foyer") is None
            and jours_ouvres_depuis(_jour_paris(_champ(lead, "consent_client_at")), aujourd_hui)
            >= settings.mer_delai_contact_jours_ouvres)


def declarations(lead) -> set[str]:
    return {d["type"] for d in (_champ(lead, "declarations_foyer") or [])}


def ecarts(lead) -> list[dict]:
    """Les CONTRADICTIONS entre foyer et partenaire ; un silence d'un côté n'en est pas une."""
    out = []
    faites = declarations(lead)
    statut = _champ(lead, "statut")
    if _champ(lead, "contact_foyer") == "non" and contact_declare_par_partenaire(lead):
        out.append({"sujet": "contact", "foyer": "Pas contacté",
                    "partenaire": f"Contacté{(' le ' + _champ(lead, 'contacte_le').strftime('%d/%m/%Y')) if _champ(lead, 'contacte_le') else ''}"})
    if "travaux_signes" in faites and statut == "perdu":
        out.append({"sujet": "signature", "foyer": "Travaux signés", "partenaire": "Sans suite"})
    if statut == "signe" and "projet_abandonne" in faites and "travaux_signes" not in faites:
        out.append({"sujet": "signature", "foyer": "Projet abandonné", "partenaire": "Signé"})
    return out


def etape(lead) -> str:
    """Où en est la demande, vue du foyer : la plus avancée des deux déclarations."""
    faites = declarations(lead)
    statut = _champ(lead, "statut")
    if _champ(lead, "consent_retire_at") is not None:
        return "retiree"
    if "travaux_signes" in faites or statut == "signe":
        return "signee"
    if "projet_abandonne" in faites or statut == "perdu":
        return "sans_suite"
    if "devis_recu" in faites or statut == "devis":
        return "devis"
    if contact_declare_par_partenaire(lead) or _champ(lead, "contact_foyer") == "oui":
        return "contactee"
    return "transmise"


# --- Indicateurs ---------------------------------------------------------------------------------


def _ratio(n: int, d: int):
    return round(100 * n / d, 1) if d else None


def _indic(cle, libelle, valeur, unite, source, n=None, d=None) -> dict:
    return {"cle": cle, "libelle": libelle, "valeur": valeur, "unite": unite, "source": source,
            "numerateur": n, "denominateur": d}


def indicateurs(leads, contestations, maisons_etudiees: set, notes: dict, mois: str | None = None) -> list[dict]:
    """`leads` : mises en relation `travaux` (déjà filtrées démo ou non) ; `maisons_etudiees` :
    maisons ayant un pré-audit ou une étude du simulateur ; `notes` : lead_id → note (1-5).
    `mois` « AAAA-MM » (mois de transmission à Paris) ou None pour le cumul."""
    leads = [l for l in leads if _champ(l, "type") == "travaux"
             and (mois is None or mois_de(_champ(l, "consent_client_at")) == mois)]
    ids = {_champ(l, "id") for l in leads}
    conts = [c for c in contestations if _champ(c, "lead_id") in ids]
    attente = {_champ(c, "lead_id") for c in conts if _champ(c, "statut") == "en_attente"}
    n = len(leads)
    demandeuses = {_champ(l, "house_id") for l in leads}
    delais = [(_champ(l, "contacte_le") - _jour_paris(_champ(l, "consent_client_at"))).days
              for l in leads if _champ(l, "contacte_le") is not None]
    non = sum(_champ(l, "contact_foyer") == "non" for l in leads)
    acceptees = sum(_champ(c, "statut") == "acceptee" for c in conts)
    devis_p = sum(_champ(l, "statut") in ("devis", "signe") for l in leads)
    signe_p = sum(_champ(l, "statut") == "signe" for l in leads)
    devis_f = sum(bool(declarations(l) & {"devis_recu", "travaux_signes"}) for l in leads)
    signe_f = sum("travaux_signes" in declarations(l) for l in leads)
    les_notes = [notes[i] for i in ids if i in notes]
    total = sum(float(_champ(l, "prix_ht") or 0) for l in leads
                if _champ(l, "prix_ht") is not None and _champ(l, "facturable") and _champ(l, "id") not in attente)
    etudiees_demandeuses = len(demandeuses & maisons_etudiees)
    return [
        _indic("transmises", "Mises en relation transmises", n, "", "calculé"),
        _indic("foyers_etude", "Foyers avec pré-audit ou étude qui demandent une mise en relation",
               _ratio(etudiees_demandeuses, len(maisons_etudiees)), "%", "calculé",
               etudiees_demandeuses, len(maisons_etudiees)),
        _indic("delai_contact", "Délai moyen de premier contact", round(mean(delais), 1) if delais else None,
               "jours", "déclaré partenaire", len(delais), n),
        _indic("non_contacte", "« Non contacté » signalés", _ratio(non, n), "%", "déclaré foyer", non, n),
        _indic("contestation", "Taux de contestation", _ratio(len(conts), n), "%", "calculé", len(conts), n),
        _indic("acceptation", "Contestations acceptées", _ratio(acceptees, len(conts)), "%", "calculé",
               acceptees, len(conts)),
        _indic("devis_partenaire", "Devis", _ratio(devis_p, n), "%", "déclaré partenaire", devis_p, n),
        _indic("devis_foyer", "Devis", _ratio(devis_f, n), "%", "déclaré foyer", devis_f, n),
        _indic("signature_partenaire", "Signatures", _ratio(signe_p, n), "%", "déclaré partenaire", signe_p, n),
        _indic("signature_foyer", "Signatures", _ratio(signe_f, n), "%", "déclaré foyer", signe_f, n),
        _indic("note", "Note moyenne", round(mean(les_notes), 2) if les_notes else None, "/5", "déclaré foyer",
               len(les_notes), None),
        _indic("total_ht", "Total HT facturable", round(total, 2), "€", "calculé"),
    ]
