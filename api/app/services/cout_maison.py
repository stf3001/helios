"""Ce que coûte la maison, et ce que les travaux changeraient (carnet, lot 10) — pur.

AUCUN NOUVEAU CALCUL DE FOND. Ce module assemble :
- l'électricité : consommation déclarée × prix du kWh de `config.py` (TRV, celui du
  pré-audit et du simulateur) — calculée, à prix supposé, avec sa date de valeur ;
- l'entretien : la somme des coûts du journal sur 12 mois — calculée sur du déclaré ;
- les charges que le foyer déclare (`charges_maison`) ;
- l'effet des travaux : le dernier pré-audit et les études du simulateur, RECOPIÉS tels
  qu'ils ont été calculés, datés. Rien n'est recalculé.

Un poste vide est « Non renseigné » (`montant_eur: None`), jamais 0 ; un poste qui ne
s'applique pas au foyer (taxe foncière d'un locataire, copropriété d'une maison) est omis.
Hélios n'est pas un outil bancaire : ni valeur du bien, ni prêt, ni patrimoine.
"""
from datetime import date, datetime

from app.core.config import settings
from app.services.autre_energie import ENERGIE_DU_TYPE, kwh_autre_energie
from app.services.simu_engine import prix_kwh

# Les entrées de journal qui sont un coût de POSSESSION. Une amélioration ou un remplacement
# est un investissement : il vit dans les projets, il ne gonfle pas le coût d'une année.
TYPES_ENTRETIEN = ("entretien", "controle", "reparation", "autre")

POSTES_DECLARES = (
    ("assurance", "assurance_eur_an"), ("taxe_fonciere", "taxe_fonciere_eur_an"),
    ("charges_copro", "charges_copro_eur_an"), ("eau", "eau_eur_an"), ("autre", "autre_eur_an"),
)


def _champ(obj, nom):
    if obj is None:
        return None
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _il_y_a_un_an(aujourd_hui: date) -> date:
    try:
        return aujourd_hui.replace(year=aujourd_hui.year - 1)
    except ValueError:  # 29 février
        return aujourd_hui.replace(year=aujourd_hui.year - 1, day=28)


def _poste(code, montant, statut, **extra) -> dict:
    return {"code": code, "montant_eur": None if montant is None else round(montant, 2),
            "statut": statut if montant is not None else None, **extra}


def poste_electricite(house) -> dict:
    """Consommation × prix du kWh (hors abonnement). La puissance souscrite choisit le prix ;
    inconnue, c'est celle que suppose le pré-audit, et la ligne le dit."""
    conso = _champ(house, "conso_elec_kwh_an")
    kva_fiche = _champ(house, "puissance_souscrite")
    kva = int(kva_fiche) if kva_fiche else settings.audit_puissance_kva_defaut
    prix = prix_kwh(kva)
    if not conso:
        return _poste("electricite", None, None)
    return _poste("electricite", conso * prix, "calcule", conso_kwh_an=conso, prix_eur_kwh=prix,
                  prix_statut="suppose", prix_date=dict(settings.audit_prix_energie_date_valeur)["electricite"],
                  kva=kva, kva_suppose=not kva_fiche)


def poste_autre_energie(house) -> dict:
    """Quantité déclarée → kWh (`autre_energie`, la conversion du pré-audit) × prix du kWh de
    cette énergie (`config.py`, bûches et granulés au prix du bois), à prix supposé et daté.
    Une ancienne quantité sans unité n'est multipliée par aucun prix : le poste le dit."""
    type_ = _champ(house, "conso_autre_energie_type")
    qte = _champ(house, "conso_autre_energie_qte")
    unite = _champ(house, "conso_autre_energie_unite")
    kwh = kwh_autre_energie(type_, unite, qte)
    if kwh is None:
        raison = "unite_inconnue" if type_ and qte and not unite else None
        return _poste("autre_energie", None, None, type_energie=type_, raison=raison)
    energie = ENERGIE_DU_TYPE[type_]
    prix = dict(settings.audit_prix_energie_eur_kwh)[energie]
    return _poste("autre_energie", kwh * prix, "calcule", type_energie=type_, quantite=qte, unite=unite,
                  conso_kwh_an=round(kwh), prix_eur_kwh=prix, prix_statut="suppose",
                  prix_date=dict(settings.audit_prix_energie_date_valeur)[energie], raison=None)


def poste_entretien(entrees, aujourd_hui: date) -> dict:
    """Somme des coûts du journal des 12 derniers mois (entretien, contrôle, réparation, autre)."""
    debut = _il_y_a_un_an(aujourd_hui)
    retenues = [e for e in entrees
                if _champ(e, "cout_eur") is not None and _champ(e, "type") in TYPES_ENTRETIEN
                and debut < _champ(e, "date") <= aujourd_hui]
    if not retenues:
        return _poste("entretien", None, None, nb_entrees=0, depuis=debut.isoformat())
    return _poste("entretien", sum(_champ(e, "cout_eur") for e in retenues), "calcule",
                  donnees="declare", nb_entrees=len(retenues), depuis=debut.isoformat())


def postes_applicables(house) -> list[str]:
    statut = _champ(house, "statut")
    codes = ["electricite", "autre_energie", "entretien", "assurance"]
    if statut in (None, "proprietaire"):  # un statut inconnu vaut propriétaire occupant (lot 8)
        codes.append("taxe_fonciere")
    if _champ(house, "type_logement") == "appartement":
        codes.append("charges_copro")
    return codes + ["eau", "autre"]


def cout_possession(house, charges, journal, aujourd_hui: date) -> dict:
    """Postes, total par an et par mois, et ce qui manque. Le total n'additionne que ce qui
    est renseigné — `postes_manquants` dit ce qu'il ne compte pas."""
    calcules = {"electricite": poste_electricite(house), "autre_energie": poste_autre_energie(house),
                "entretien": poste_entretien(journal, aujourd_hui)}
    for code, champ in POSTES_DECLARES:
        extra = {"libelle": _champ(charges, "autre_libelle")} if code == "autre" else {}
        calcules[code] = _poste(code, _champ(charges, champ), "declare", **extra)
    postes = [calcules[c] for c in postes_applicables(house)]
    renseignes = [p for p in postes if p["montant_eur"] is not None]
    total = round(sum(p["montant_eur"] for p in renseignes), 2) if renseignes else None
    return {
        "postes": postes,
        "total_an_eur": total,
        "total_mois_eur": None if total is None else round(total / 12, 2),
        "postes_manquants": [p["code"] for p in postes if p["montant_eur"] is None],
    }


# ------------------------------------------------------------------ effet des travaux

def _jour(d) -> str | None:
    if d is None:
        return None
    return (d.date() if isinstance(d, datetime) else d).isoformat()


def effet_travaux(dernier_audit, etudes) -> dict:
    """Le plan du dernier pré-audit et les études du simulateur, TELS QU'ILS ONT ÉTÉ CALCULÉS.

    `dernier_audit` : (json_result, created_at, id) ou None ; `etudes` : [(resultat, created_at,
    id, nom)]. Les formats d'audit sans `priorites` chiffrées (v1) ne donnent pas d'actions.
    """
    audit = None
    if dernier_audit is not None:
        json_result, cree_le, audit_id = dernier_audit
        actions = []
        for p in (json_result or {}).get("priorites") or []:
            if not isinstance(p, dict) or not isinstance(p.get("cout_eur"), dict):
                continue
            actions.append({
                "action": p.get("action"), "label": p.get("label"), "horizon": p.get("horizon"),
                "cout_eur": p.get("cout_eur"), "economie_annuelle_eur": p.get("economie_annuelle_eur"),
                "temps_retour_ans": p.get("temps_retour_ans"), "statuts": p.get("statuts") or {},
            })
        audit = {"id": str(audit_id), "date": _jour(cree_le), "actions": actions,
                 "plan_recommande": ((json_result or {}).get("synthese") or {}).get("plan_recommande")}
    simulations = []
    for resultat, cree_le, etude_id, nom in etudes:
        ind = (resultat or {}).get("indicateurs") or {}
        inv = (resultat or {}).get("investissement") or {}
        simulations.append({
            "id": str(etude_id), "date": _jour(cree_le), "nom": nom,
            "investissement_eur": inv.get("total_eur"), "economie_1re_annee_eur": ind.get("economie_1re_annee_eur"),
            "temps_retour_ans": ind.get("temps_retour_ans"), "puissance_kwc": ind.get("puissance_kwc"),
        })
    return {"audit": audit, "etudes": simulations}
