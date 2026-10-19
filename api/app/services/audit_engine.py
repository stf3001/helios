"""Moteur déterministe de pré-audit — doc 07 §6, version v2.

Pipeline : fiche Maison → consommation de CHAUFFAGE en énergie finale (DPE ou année de
construction, corrigée du climat) → calage sur la facture quand le chauffage est électrique
→ déperditions par poste → actions chiffrées, combinées dans l'ordre du plan, rangées en
trois horizons (maintenant / prioritaire / à l'occasion).

RÈGLE ABSOLUE (doc 07 §5-6) : tous les chiffres sortent d'ici, JAMAIS du LLM. Toutes les
valeurs de référence vivent dans `audit_reference.py` ou `config.py` (`audit_*`), et le
pré-audit dit lesquelles il a utilisées (bloc `hypotheses`) et d'où vient chaque entrée
(bloc `entrees`). Les audits v1 déjà stockés ne sont jamais recalculés.

Statuts d'un chiffre : `observe` (mesuré), `declare` (saisi dans la fiche), `suppose`
(hypothèse faute de donnée), `calcule` (dérivé par le moteur).
"""

from app.core.config import settings
from app.models.house import House
from app.services import audit_reference as ref
from app.services.completeness import compute_score, niveau_for_score
from app.services.regions import departement_du_code_postal
from app.services.simu_engine import prix_kwh as prix_electricite_kwh


def _grille(table: tuple[tuple, ...], cle):
    """Lit une grille de config. Lève si la clé manque : aucun repli silencieux."""
    return dict(table)[cle]


def _fourchette(value: float) -> dict:
    demi = settings.audit_incertitude
    return {"bas": round(value * (1 - demi)), "haut": round(value * (1 + demi)), "central": round(value)}


class _Trace:
    """Ce que le moteur a lu dans la fiche, et les valeurs de référence qu'il a utilisées."""

    def __init__(self):
        self.entrees: list[dict] = []
        self.hypotheses: dict[str, dict] = {}
        self.alertes: list[str] = []

    def entree(self, champ: str, valeur, hypothese: str | None = None):
        if valeur is None or valeur == []:
            self.entrees.append({"champ": champ, "valeur": None, "statut": "suppose",
                                 "hypothese": hypothese or "inconnu, non utilisé"})
        else:
            self.entrees.append({"champ": champ, "valeur": valeur, "statut": "declare"})

    def hyp(self, cle: str, valeur, source: str):
        texte, date = ref.SOURCES[source]
        self.hypotheses[cle] = {"cle": cle, "valeur": valeur, "source": texte, "date": date}

    def hyp_fiche(self, cle: str, valeur: str):
        """Une hypothèse qui tient à la fiche elle-même, pas à une valeur de référence."""
        self.hypotheses[cle] = {"cle": cle, "valeur": valeur, "source": "Fiche Maison", "date": None}


# --- Lecture de la fiche --------------------------------------------------------------------

def zone_climatique(code_postal: str | None) -> tuple[str, bool]:
    """Zone H1/H2/H3 du département, et si elle a été SUPPOSÉE (code postal illisible)."""
    dep = departement_du_code_postal(code_postal or "")
    if dep in ref.ZONE_CLIMATIQUE:
        return ref.ZONE_CLIMATIQUE[dep], False
    return settings.audit_zone_defaut, True


def _profil(house: House, t: _Trace) -> dict:
    """Valeurs de la fiche utilisées par le moteur, avec leurs hypothèses quand elles manquent."""
    surface = house.surface_habitable or 0
    t.entree("surface_habitable", house.surface_habitable, "inconnue → aucun chiffrage au m²")
    if not surface:
        t.alertes.append("Surface habitable inconnue : les postes chiffrés au m² ne peuvent pas l'être.")

    niveaux = house.nb_niveaux or 1
    t.entree("nb_niveaux", house.nb_niveaux, "inconnu → 1 niveau (combles et plancher = surface habitable)")

    occupants = house.nb_occupants if house.nb_occupants is not None else settings.audit_occupants_defaut
    t.entree("nb_occupants", house.nb_occupants, f"inconnu → {settings.audit_occupants_defaut} occupants")

    zone, zone_supposee = zone_climatique(house.code_postal)
    t.entree("code_postal", house.code_postal)
    t.hyp("zone_climatique", zone + (" (supposée)" if zone_supposee else ""), "zone_climatique")

    chauffage = house.chauffage_principal or ref.CHAUFFAGE_DEFAUT
    t.entree("chauffage_principal", house.chauffage_principal,
             f"inconnu → {ref.CHAUFFAGE_DEFAUT} (cas le plus courant)")
    energie = ref.ENERGIE_CHAUFFAGE[chauffage]
    if chauffage == "autre":
        t.hyp_fiche("energie_chauffage_autre", "chauffage « autre » traité comme électrique")

    ecs = house.ecs or settings.audit_ecs_defaut
    t.entree("ecs", house.ecs, f"inconnue → {settings.audit_ecs_defaut}")

    kva = int(house.puissance_souscrite) if house.puissance_souscrite else settings.audit_puissance_kva_defaut
    t.entree("puissance_souscrite", house.puissance_souscrite,
             f"inconnue → {settings.audit_puissance_kva_defaut} kVA")

    for champ in ("annee_construction", "dpe_lettre", "isolation_combles", "isolation_murs",
                  "isolation_plancher", "menuiseries", "ventilation", "regulation", "clim",
                  "conso_elec_kwh_an", "objectifs"):
        t.entree(champ, getattr(house, champ))

    return {"surface": surface, "niveaux": niveaux, "occupants": occupants, "zone": zone,
            "zone_supposee": zone_supposee, "chauffage": chauffage, "energie": energie,
            "ecs": ecs, "kva": kva}


def prix_energie(energie: str, kva: int) -> float:
    if energie == "electricite":
        return prix_electricite_kwh(kva)
    return _grille(settings.audit_prix_energie_eur_kwh, energie)


# --- Consommation de chauffage --------------------------------------------------------------

def conso_chauffage_estimee(house: House, p: dict, t: _Trace) -> dict:
    """Consommation de chauffage théorique, en kWh d'ÉNERGIE FINALE de l'énergie du chauffage."""
    surface, chauffage, energie = p["surface"], p["chauffage"], p["energie"]
    lettre = (house.dpe_lettre or "").upper()
    if lettre in ref.DPE_KWH_EP_M2_AN:
        ep = ref.DPE_KWH_EP_M2_AN[lettre]
        coef = _grille(settings.audit_coef_ep_ef, energie)
        part = _grille(settings.audit_part_chauffage_dpe, chauffage)
        t.hyp(f"dpe_kwh_ep_m2_an[{lettre}]", ep, "dpe_kwh_ep_m2_an")
        t.hyp(f"coef_ep_ef[{energie}]", coef, "coef_ep_ef")
        t.hyp(f"part_chauffage_dpe[{chauffage}]", part, "part_chauffage_dpe")
        conso = ep * surface / coef * part
        detail = {"dpe_kwh_ep_m2_an": ep, "coef_ep_ef": coef, "part_chauffage": part}
        origine = "dpe"
    else:
        annee = house.annee_construction or ref.ANNEE_DEFAUT
        origine = "annee_construction" if house.annee_construction else "defaut"
        besoin = ref.ANNEE_BESOIN_UTILE_KWH_M2_AN[annee]
        coef_zone = _grille(settings.audit_coef_zone, p["zone"])
        rendement = _grille(settings.audit_rendement_chauffage, chauffage)
        t.hyp(f"besoin_utile_kwh_m2_an[{annee}]", besoin, "besoin_utile_kwh_m2_an")
        t.hyp(f"coef_zone[{p['zone']}]", coef_zone, "coef_zone")
        t.hyp(f"rendement_chauffage[{chauffage}]", rendement, "rendement_chauffage")
        t.hyp("altitude", "ignorée en v2", "coef_zone")
        conso = besoin * surface * coef_zone / rendement
        detail = {"besoin_utile_kwh_m2_an": besoin, "coef_zone": coef_zone, "rendement": rendement}
    return {
        "conso_chauffage_estimee_kwh_an": round(conso),
        "energie_chauffage": energie,
        "origine": origine,  # dpe | annee_construction | defaut
        "zone_climatique": p["zone"],
        "surface_m2": surface,
        "detail_estimation": detail,
    }


def usages_specifiques_kwh(house: House, p: dict, t: _Trace) -> int:
    """Électricité hors chauffage : mêmes couches que le simulateur (`simu_conso_*`)."""
    occ = max(p["occupants"], 1)
    base = settings.simu_conso_base_fixe_kwh_an + settings.simu_conso_base_par_occupant_kwh_an * occ
    ecs = _grille(settings.simu_conso_ecs_kwh_occupant_an, p["ecs"]) * occ
    clim = settings.simu_conso_clim_kwh_piece_an * settings.audit_clim_pieces_defaut if house.clim else 0
    t.hyp("usages_specifiques_kwh_an",
          {"base": round(base), "eau_chaude": round(ecs), "climatisation": round(clim)}, "usages_specifiques")
    if house.clim:
        t.hyp("clim_pieces", settings.audit_clim_pieces_defaut, "usages_specifiques")
    return round(base + ecs + clim)


def message_ratio(ratio: float) -> str:
    for borne, message in settings.audit_ratio_messages:
        if ratio < borne:
            return message
    return settings.audit_ratio_messages[-1][1]


def consommation(house: House, p: dict, t: _Trace) -> dict:
    """Estimation, puis calage sur la facture électrique quand c'est possible."""
    c = conso_chauffage_estimee(house, p, t)
    estimee = c["conso_chauffage_estimee_kwh_an"]
    statuts = {"conso_chauffage_estimee_kwh_an": "calcule" if c["origine"] != "defaut" else "suppose"}
    c.update({"conso_elec_declaree_kwh_an": house.conso_elec_kwh_an, "usages_specifiques_kwh_an": None,
              "conso_chauffage_declaree_kwh_an": None, "ratio_reel_theorique": None, "message_ratio": None})

    retenue, base = estimee, "estimee"
    if p["energie"] == "electricite" and house.conso_elec_kwh_an:
        usages = usages_specifiques_kwh(house, p, t)
        declaree = max(0, house.conso_elec_kwh_an - usages)
        c["usages_specifiques_kwh_an"] = usages
        c["conso_chauffage_declaree_kwh_an"] = declaree
        statuts.update({"conso_elec_declaree_kwh_an": "declare", "usages_specifiques_kwh_an": "suppose",
                        "conso_chauffage_declaree_kwh_an": "calcule"})
        if declaree < settings.audit_chauffage_declare_min_kwh:
            t.alertes.append(
                f"Incohérence : une fois retirés les usages courants (~{usages} kWh), la consommation "
                f"déclarée ({house.conso_elec_kwh_an} kWh) ne laisse presque rien pour le chauffage. "
                "Les économies sont calculées sur l'estimation, à confirmer avec vos factures."
            )
        else:
            retenue, base = declaree, "declaree"
        if estimee:
            ratio = round(declaree / estimee, 2)
            c["ratio_reel_theorique"] = ratio
            c["message_ratio"] = message_ratio(ratio)
            statuts["ratio_reel_theorique"] = "calcule"
    elif p["energie"] != "electricite":
        if house.conso_autre_energie_qte:
            t.hyp_fiche("conso_autre_energie",
                        "non utilisée : la fiche ne précise pas l'unité de la quantité saisie")
        t.hyp_fiche("base_economies", "consommation estimée (pas de relevé de cette énergie)")

    prix = prix_energie(p["energie"], p["kva"])
    t.hyp(f"prix_{p['energie']}_eur_kwh", prix, f"prix_{p['energie']}")
    statuts.update({"conso_chauffage_retenue_kwh_an": "calcule" if base == "declaree" else statuts[
        "conso_chauffage_estimee_kwh_an"], "prix_energie_eur_kwh": "suppose", "cout_chauffage_actuel_eur": "calcule"})
    c.update({
        "conso_chauffage_retenue_kwh_an": retenue,
        "base_economies": base,  # declaree | estimee
        "prix_energie_eur_kwh": prix,
        "cout_chauffage_actuel_eur": round(retenue * prix),
        "statuts": statuts,
    })
    return c


# --- Déperditions ---------------------------------------------------------------------------

def _etat(valeur: str | None) -> str:
    return valeur if valeur is not None else "inconnue"


def deperditions(house: House) -> list[dict]:
    """Répartition des déperditions par poste (en %), modulée par l'état réel. Somme = 100 %."""
    etats = {
        "toiture": (ref.QUALITE_ISOLATION, _etat(house.isolation_combles)),
        "murs": (ref.QUALITE_ISOLATION, _etat(house.isolation_murs)),
        "plancher": (ref.QUALITE_ISOLATION, _etat(house.isolation_plancher)),
        "menuiseries": (ref.QUALITE_MENUISERIES, _etat(house.menuiseries)),
        "air_ventilation": (ref.QUALITE_VENTILATION, _etat(house.ventilation)),
    }
    coeffs = {poste: table[etat] for poste, (table, etat) in etats.items()}
    coeffs["ponts_thermiques"] = ref.PONTS_THERMIQUES_COEF
    inconnus = {poste for poste, (_, etat) in etats.items() if etat == "inconnue"} | {"ponts_thermiques"}

    poids = {poste: ref.DEPERDITION_BASE[poste] * coeffs[poste] for poste in ref.DEPERDITION_BASE}
    total = sum(poids.values()) or 1.0
    return [
        {"poste": poste, "part_pct": round(100 * p / total, 1),
         "statut": "suppose" if poste in inconnus else "calcule"}
        for poste, p in sorted(poids.items(), key=lambda kv: kv[1], reverse=True)
    ]


# --- Actions --------------------------------------------------------------------------------

def _gain_local(key: str, house: House) -> float:
    """Gain de l'action sur le chauffage, modulé par l'état du poste (un poste à moitié
    isolé rapporte moins qu'un poste nu)."""
    a = ref.ACTIONS[key]
    coef = {
        "isolation_combles": ref.QUALITE_ISOLATION[_etat(house.isolation_combles)],
        "isolation_murs": ref.QUALITE_ISOLATION[_etat(house.isolation_murs)],
        "isolation_plancher": ref.QUALITE_ISOLATION[_etat(house.isolation_plancher)],
        "menuiseries": ref.QUALITE_MENUISERIES[_etat(house.menuiseries)],
        "ventilation_double_flux": ref.QUALITE_VENTILATION[_etat(house.ventilation)],
        "regulation": 1.0,
    }[key]
    return a["gain_pct_chauffage"] * coef


def _action_recommandee(key: str, house: House, chauffage: str) -> bool:
    """Une action est recommandée si le poste correspondant est mal traité dans la fiche."""
    if key == "isolation_combles":
        return ref.ISOLATION_A_TRAITER[_etat(house.isolation_combles)]
    if key == "isolation_murs":
        return ref.ISOLATION_A_TRAITER[_etat(house.isolation_murs)]
    if key == "isolation_plancher":
        return ref.ISOLATION_A_TRAITER[_etat(house.isolation_plancher)]
    if key == "menuiseries":
        return ref.MENUISERIES_A_REMPLACER[_etat(house.menuiseries)]
    if key == "ventilation_double_flux":
        return ref.VENTILATION_A_REMPLACER[_etat(house.ventilation)]
    if key == "pac_air_eau":
        return chauffage in ref.CHAUFFAGE_A_REMPLACER
    if key == "regulation":
        # Régulation non renseignée : supposée absente (hypothèse prudente, déjà v1).
        return ref.REGULATION_A_AMELIORER[house.regulation or "aucune"]
    return False


def ratio_murs(niveaux: int) -> float:
    ratio = None
    for n, r in sorted(settings.audit_ratio_murs_par_niveaux):
        if niveaux >= n or ratio is None:
            ratio = r
    return ratio


def _quantite(action: dict, p: dict) -> tuple[float, str]:
    unit, surface = action["unit"], p["surface"]
    if unit == "m2_emprise":
        return round(surface / p["niveaux"]), "m²"
    if unit == "m2_mur":
        return round(surface * ratio_murs(p["niveaux"])), "m² de mur"
    if unit == "fenetre":
        return max(1, round(surface / ref.M2_PAR_FENETRE)), "fenêtre(s)"
    return 1, "forfait"


def _actions_candidates(house: House, p: dict, deps: list[dict], t: _Trace) -> list[dict]:
    part_par_poste = {d["poste"]: d["part_pct"] for d in deps}
    actions = []
    for key, a in ref.ACTIONS.items():
        if not _action_recommandee(key, house, p["chauffage"]):
            continue
        qte, unite = _quantite(a, p)
        cout_bas, cout_haut = round(a["cout_bas"] * qte), round(a["cout_haut"] * qte)
        central = (cout_bas + cout_haut) / 2
        aide = {"bas": round(central * a["aide_pct_bas"]), "haut": round(central * a["aide_pct_haut"])}
        actions.append({
            "action": key,
            "label": a["label"],
            "poste": a["poste"],
            "part_deperdition_pct": part_par_poste.get(a["poste"]),
            "quantite": {"valeur": qte, "unite": unite},
            "cout_unitaire_eur": {"bas": a["cout_bas"], "haut": a["cout_haut"], "unite": unite},
            "cout_eur": {"bas": cout_bas, "haut": cout_haut},
            "aide_estimee_eur": aide,
            "reste_a_charge_eur": {"bas": round(central - aide["haut"]), "haut": round(central - aide["bas"])},
            "aides_statut": "a_verifier",
            "_reste_central": central - (aide["bas"] + aide["haut"]) / 2,
            "gain_pct_chauffage": None if key == "pac_air_eau" else round(_gain_local(key, house), 3),
            "duree_vie_ans": a["duree_vie_ans"],
            "libelle_occasion": a["libelle_occasion"],
            "priorite_hierarchie": a["priorite_hierarchie"],
            "statuts": {
                "quantite": "suppose", "cout_eur": "suppose", "aide_estimee_eur": "suppose",
                "economie_annuelle_eur": "calcule", "temps_retour_ans": "calcule",
                "part_deperdition_pct": next((d["statut"] for d in deps if d["poste"] == a["poste"]), None),
            },
        })
    if actions:
        t.hyp("couts_actions", {a["action"]: [a["cout_unitaire_eur"]["bas"], a["cout_unitaire_eur"]["haut"],
                                              a["cout_unitaire_eur"]["unite"]] for a in actions}, "couts_actions")
        t.hyp("aides_pct", {a: [ref.ACTIONS[a]["aide_pct_bas"], ref.ACTIONS[a]["aide_pct_haut"]]
                            for a in (x["action"] for x in actions)}, "aides")
        t.hyp("gains_pct_chauffage", {a["action"]: a["gain_pct_chauffage"] for a in actions
                                      if a["gain_pct_chauffage"] is not None}, "gains_actions")
        if any(a["action"] == "isolation_murs" for a in actions):
            t.hyp(f"ratio_murs[{p['niveaux']} niveau(x)]", ratio_murs(p["niveaux"]), "ratio_murs")
    return actions


def _appliquer(ordre: list[dict], conso: float, energie: str, prix: float, chauffage: str, kva: int) -> float:
    """Combinaison séquentielle : chaque action porte sur ce qui reste après les précédentes.

    Renvoie le coût annuel du chauffage une fois tout le plan réalisé. L'économie inscrite
    sur chaque action est son économie MARGINALE à sa place dans le plan.
    """
    rendement = _grille(settings.audit_rendement_chauffage, chauffage)
    scop = _grille(settings.audit_rendement_chauffage, "PAC_air_eau")
    prix_elec = prix_energie("electricite", kva)
    for a in ordre:
        if a["action"] == "pac_air_eau":
            apres = conso * rendement / scop
            eur = conso * prix - apres * prix_elec
            a["economie_annuelle_kwh"] = None  # changement d'énergie : des kWh qui ne se soustraient pas
            a["conso_apres_kwh_electricite"] = round(apres)
            conso, prix, rendement, energie = apres, prix_elec, scop, "electricite"
        else:
            kwh = conso * a["gain_pct_chauffage"]
            eur = kwh * prix
            conso -= kwh
            a["economie_annuelle_kwh"] = round(kwh)
            a["energie_economisee"] = energie
        a["economie_annuelle_eur"] = _fourchette(eur)
        a["temps_retour_ans"] = round(a["_reste_central"] / eur, 1) if eur > 0 else None
    return conso * prix


def _horizon(a: dict, deja_occasion: set[str]) -> str:
    if a["action"] in deja_occasion:
        return "a_l_occasion"
    if a["priorite_hierarchie"] == 1 or a["cout_eur"]["haut"] <= settings.audit_horizon_cout_max_eur:
        return "maintenant"
    retour = a["temps_retour_ans"]
    if retour is not None and retour <= settings.audit_horizon_retour_max_ans and retour <= a["duree_vie_ans"]:
        return "prioritaire"
    return "a_l_occasion"


def _objectif_facture(objectifs: list[str] | None) -> bool:
    return any("factur" in o.lower() or "économ" in o.lower() or "econom" in o.lower() for o in objectifs or [])


def planifier(actions: list[dict], c: dict, p: dict, objectifs: list[str] | None) -> float:
    """Classe les actions (horizon → hiérarchie → critère secondaire) et les chiffre en séquence.

    Horizon et économies marginales dépendent l'un de l'autre : on itère. Une action passée
    « à l'occasion » y reste — son économie ne peut que baisser en reculant dans le plan —
    donc les horizons se stabilisent en au plus n tours ; la borne large ne sert qu'à
    l'objectif « facture », où l'ordre suit le temps de retour. Renvoie le coût final.
    """
    facture = _objectif_facture(objectifs)
    etat = (c["conso_chauffage_retenue_kwh_an"], c["energie_chauffage"], c["prix_energie_eur_kwh"],
            p["chauffage"], p["kva"])

    def cle(a: dict):
        retour = a["temps_retour_ans"] if a["temps_retour_ans"] is not None else 99
        secondaire = retour if facture else -(a.get("part_deperdition_pct") or 0)
        return (ref.HORIZONS.index(a["horizon"]), a["priorite_hierarchie"], secondaire)

    # Premier passage : chaque action seule, sur la maison actuelle.
    for a in actions:
        _appliquer([a], *etat)
    occasion: set[str] = set()
    ordre, signature = actions, None
    for _ in range(50):
        for a in ordre:
            a["horizon"] = _horizon(a, occasion)
            if a["horizon"] == "a_l_occasion":
                occasion.add(a["action"])
        ordre = sorted(ordre, key=cle)
        cout_final = _appliquer(ordre, *etat)
        nouvelle = [(a["action"], _horizon(a, occasion)) for a in ordre]
        if nouvelle == signature:
            break
        signature = nouvelle
    actions[:] = ordre
    for i, a in enumerate(actions, 1):
        a["rang"] = i
        a.pop("_reste_central", None)
        if a["horizon"] != "a_l_occasion":
            a["libelle_occasion"] = None
    return cout_final if actions else c["cout_chauffage_actuel_eur"]


def run_audit(house: House) -> dict:
    """Produit le JSON structuré complet du pré-audit (sans texte LLM — chiffres déterministes)."""
    t = _Trace()
    score = compute_score(house)
    p = _profil(house, t)
    c = consommation(house, p, t)
    dep = deperditions(house)
    t.hyp("deperditions_base", ref.DEPERDITION_BASE, "deperditions")
    actions = _actions_candidates(house, p, dep, t)
    cout_final = planifier(actions, c, p, house.objectifs)
    t.hyp("horizons", {"cout_max_eur": settings.audit_horizon_cout_max_eur,
                       "retour_max_ans": settings.audit_horizon_retour_max_ans}, "horizons")
    t.hyp("incertitude", settings.audit_incertitude, "incertitude")

    cout_actuel = c["conso_chauffage_retenue_kwh_an"] * c["prix_energie_eur_kwh"]
    economie_total = cout_actuel - cout_final
    centrals = [(a["cout_eur"]["bas"] + a["cout_eur"]["haut"]) / 2 for a in actions]
    a_faire = [a for a in actions if a["horizon"] != "a_l_occasion"]

    return {
        "version_helios": settings.audit_version,
        "completeness_score": score,
        "niveau": niveau_for_score(score),
        "entrees": t.entrees,
        "deperditions": dep,
        "deperditions_statut": "suppose" if any(d["statut"] == "suppose" and d["poste"] != "ponts_thermiques"
                                                 for d in dep) else "calcule",
        "consommation": c,
        "priorites": actions,
        "synthese": {
            "nb_actions": len(actions),
            "nb_par_horizon": {h: sum(a["horizon"] == h for a in actions) for h in ref.HORIZONS},
            "investissement_eur": {"bas": sum(a["cout_eur"]["bas"] for a in actions),
                                   "haut": sum(a["cout_eur"]["haut"] for a in actions)},
            "aides_estimees_eur": {"bas": sum(a["aide_estimee_eur"]["bas"] for a in actions),
                                   "haut": sum(a["aide_estimee_eur"]["haut"] for a in actions)},
            "reste_a_charge_eur": {"bas": round(sum(centrals) - sum(a["aide_estimee_eur"]["haut"] for a in actions)),
                                   "haut": round(sum(centrals) - sum(a["aide_estimee_eur"]["bas"] for a in actions))},
            "aides_statut": "a_verifier",
            "cout_chauffage_actuel_eur": round(cout_actuel),
            "economie_annuelle_totale_eur": _fourchette(economie_total) if economie_total > 0 else None,
            "economie_chauffage_pct": round(100 * economie_total / cout_actuel) if cout_actuel else None,
            # Jamais une action « à l'occasion » : si rien d'autre, pas de première étape.
            "premiere_action": a_faire[0]["label"] if a_faire else None,
        },
        "alertes": t.alertes,
        "hypotheses": list(t.hypotheses.values()),
        "avertissement": (
            "Pré-diagnostic indicatif (ordres de grandeur), ne remplace ni un DPE ni un audit "
            "énergétique réalisé par un professionnel certifié. Coûts, aides et économies à confirmer."
        ),
    }
