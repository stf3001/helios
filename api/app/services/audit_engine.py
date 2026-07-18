"""Moteur déterministe de pré-audit — doc 07 §6.

Pipeline : fiche Maison → déperditions par poste (3CL dégradé) → conso théorique vs déclarée
→ priorisation (hiérarchie constitution × objectifs) → chiffrage fourchettes coûts/aides.

RÈGLE ABSOLUE (doc 07 §5-6) : tous les chiffres sortent d'ici, JAMAIS du LLM. Le LLM ne fait
que la mise en forme rédactionnelle autour de ce JSON. Résultats reproductibles et auditables.
"""

from app.core.config import settings
from app.models.house import House
from app.services import audit_reference as ref
from app.services.completeness import compute_score, niveau_for_score


def _fourchette(value: float) -> dict:
    demi = settings.audit_incertitude
    return {"bas": round(value * (1 - demi)), "haut": round(value * (1 + demi)), "central": round(value)}


def besoin_chauffage_kwh_m2(house: House) -> tuple[int, str]:
    """Besoin de chauffage de référence (kWh/m²/an) + origine de l'estimation."""
    if house.dpe_lettre and house.dpe_lettre.upper() in ref.DPE_KWH_M2_AN:
        return ref.DPE_KWH_M2_AN[house.dpe_lettre.upper()], "dpe"
    if house.annee_construction and house.annee_construction in ref.ANNEE_KWH_M2_AN:
        return ref.ANNEE_KWH_M2_AN[house.annee_construction], "annee_construction"
    return ref._DEFAUT_KWH_M2_AN, "defaut"


def deperditions(house: House) -> list[dict]:
    """Répartition des déperditions par poste, modulée par l'état d'isolation réel. Somme = 100 %."""
    coeffs = {
        "toiture": ref.QUALITE_ISOLATION.get(house.isolation_combles, 0.85),
        "murs": ref.QUALITE_ISOLATION.get(house.isolation_murs, 0.85),
        "plancher": ref.QUALITE_ISOLATION.get(house.isolation_plancher, 0.85),
        "menuiseries": ref.QUALITE_MENUISERIES.get(house.menuiseries, 0.7),
        "air_ventilation": ref.QUALITE_VENTILATION.get(house.ventilation, 0.85),
        "ponts_thermiques": 0.7,  # non renseignable dans la fiche v1 — hypothèse fixe
    }
    poids = {poste: ref.DEPERDITION_BASE[poste] * coeffs[poste] for poste in ref.DEPERDITION_BASE}
    total = sum(poids.values()) or 1.0
    result = [
        {"poste": poste, "part_pct": round(100 * p / total, 1)}
        for poste, p in sorted(poids.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return result


def conso_theorique_vs_declaree(house: House) -> dict:
    """Conso de chauffage théorique (besoin × surface) comparée à la conso élec déclarée."""
    besoin, origine = besoin_chauffage_kwh_m2(house)
    surface = house.surface_habitable or 0
    theorique = besoin * surface
    declaree = house.conso_elec_kwh_an
    ecart_pct = None
    if declaree and theorique:
        ecart_pct = round(100 * (declaree - theorique) / theorique)
    return {
        "besoin_kwh_m2_an": besoin,
        "origine_besoin": origine,  # dpe | annee_construction | defaut
        "surface_m2": surface,
        "conso_chauffage_theorique_kwh_an": theorique,
        "conso_elec_declaree_kwh_an": declaree,
        "ecart_pct": ecart_pct,  # >0 : la conso déclarée dépasse le besoin chauffage théorique (autres usages inclus)
    }


def _quantite_action(action_key: str, action: dict, house: House) -> float:
    surface = house.surface_habitable or 0
    unit = action["unit"]
    if unit == "m2_habitable":
        return surface
    if unit == "fenetre":
        return max(1, round(surface / ref.M2_PAR_FENETRE))
    return 1  # forfait


def _action_recommandee(action_key: str, house: House) -> bool:
    """Une action est recommandée si le poste correspondant est mal traité dans la fiche."""
    if action_key == "isolation_combles":
        return house.isolation_combles in (None, "aucune", "partielle", "inconnue")
    if action_key == "isolation_murs":
        return house.isolation_murs in (None, "aucune", "partielle", "inconnue")
    if action_key == "isolation_plancher":
        return house.isolation_plancher in (None, "aucune", "partielle", "inconnue")
    if action_key == "menuiseries":
        return house.menuiseries in (None, "simple", "inconnue")
    if action_key == "ventilation_double_flux":
        return house.ventilation in (None, "aucune", "naturelle")
    if action_key == "pac_air_eau":
        return house.chauffage_principal in ref.CHAUFFAGE_A_REMPLACER
    if action_key == "regulation":
        return house.regulation in (None, "aucune")
    return False


def chiffrage(house: House, deperditions_list: list[dict]) -> list[dict]:
    """Actions recommandées, chiffrées en fourchettes, ordonnées par la hiérarchie de la constitution."""
    besoin, _ = besoin_chauffage_kwh_m2(house)
    surface = house.surface_habitable or 0
    conso_ref = house.conso_elec_kwh_an or (besoin * surface)
    part_par_poste = {d["poste"]: d["part_pct"] for d in deperditions_list}

    actions = []
    for key, action in ref.ACTIONS.items():
        if not _action_recommandee(key, house):
            continue
        qte = _quantite_action(key, action, house)
        cout_bas = round(action["cout_bas"] * qte)
        cout_haut = round(action["cout_haut"] * qte)
        cout_central = (cout_bas + cout_haut) / 2
        aide = round(cout_central * action["aide_pct"])
        reste = round(cout_central - aide)
        economie_kwh = round(conso_ref * action["gain_pct_conso"])
        economie_eur = round(economie_kwh * settings.solar_prix_achat_eur_kwh)
        retour_ans = round(reste / economie_eur, 1) if economie_eur > 0 else None
        actions.append({
            "action": key,
            "label": action["label"],
            "poste": action["poste"],
            "part_deperdition_pct": part_par_poste.get(action["poste"]),
            "cout_eur": {"bas": cout_bas, "haut": cout_haut},
            "aide_estimee_eur": aide,
            "reste_a_charge_eur": reste,
            "economie_annuelle_eur": _fourchette(economie_eur),
            "temps_retour_ans": retour_ans,
            "priorite_hierarchie": action["priorite_hierarchie"],
        })
    return actions


def _prioriser(actions: list[dict], deperditions_list: list[dict], objectifs: list[str] | None) -> list[dict]:
    """Ordonne : hiérarchie constitution (sobriété→enveloppe→systèmes) d'abord, puis part de déperdition.

    Un objectif « réduire la facture » remonte les actions à meilleur temps de retour ;
    « améliorer le confort » remonte l'enveloppe. (doc 07 §6.3)
    """
    objectifs = objectifs or []
    priv_facture = any("factur" in o.lower() or "économ" in o.lower() or "econom" in o.lower() for o in objectifs)

    def cle(a: dict):
        part = a.get("part_deperdition_pct") or 0
        retour = a.get("temps_retour_ans") or 99
        # tri primaire : niveau de hiérarchie (1=sobriété d'abord) ; secondaire selon objectif
        secondaire = retour if priv_facture else -part
        return (a["priorite_hierarchie"], secondaire)

    ordered = sorted(actions, key=cle)
    for i, a in enumerate(ordered, 1):
        a["rang"] = i
    return ordered


def run_audit(house: House) -> dict:
    """Produit le JSON structuré complet du pré-audit (sans texte LLM — chiffres déterministes)."""
    score = compute_score(house)
    dep = deperditions(house)
    conso = conso_theorique_vs_declaree(house)
    actions = _prioriser(chiffrage(house, dep), dep, house.objectifs)

    invest_total_bas = sum(a["cout_eur"]["bas"] for a in actions)
    invest_total_haut = sum(a["cout_eur"]["haut"] for a in actions)
    aides_total = sum(a["aide_estimee_eur"] for a in actions)
    economie_total = sum(a["economie_annuelle_eur"]["central"] for a in actions)

    return {
        "version_helios": settings.audit_version,
        "completeness_score": score,
        "niveau": niveau_for_score(score),
        "deperditions": dep,
        "consommation": conso,
        "priorites": actions,
        "synthese": {
            "nb_actions": len(actions),
            "investissement_eur": {"bas": invest_total_bas, "haut": invest_total_haut},
            "aides_estimees_eur": aides_total,
            "economie_annuelle_totale_eur": _fourchette(economie_total) if economie_total else None,
            "premiere_action": actions[0]["label"] if actions else None,
        },
        "avertissement": (
            "Pré-diagnostic indicatif (ordres de grandeur), ne remplace pas un audit énergétique "
            "réalisé par un professionnel certifié. Coûts, aides et économies à confirmer."
        ),
    }
