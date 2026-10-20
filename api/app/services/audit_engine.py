"""Moteur déterministe de pré-audit — doc 07 §6, version v2.3.

Pipeline : fiche Maison → consommation de CHAUFFAGE en énergie finale (DPE ou année de
construction, corrigée du climat) → calage sur la facture quand le chauffage est électrique
→ déperditions par poste → actions chiffrées, combinées dans l'ordre du plan, rangées en
trois horizons (maintenant / prioritaire / à l'occasion) → conseils sans chiffre (gestes
gratuits, âge des équipements, confort d'été) → solaire, CITÉ d'une étude du simulateur ou
proposé comme piste sans chiffre.

RÈGLE ABSOLUE (doc 07 §5-6) : tous les chiffres sortent d'ici, JAMAIS du LLM. Toutes les
valeurs de référence vivent dans `audit_reference.py` ou `config.py` (`audit_*`), et le
pré-audit dit lesquelles il a utilisées (bloc `hypotheses`) et d'où vient chaque entrée
(bloc `entrees`). Les audits déjà stockés (v1, v2) ne sont jamais recalculés.

Le moteur est PUR : aucun accès réseau ni base. L'étude du simulateur lui est passée par
la route (`resume_etude_simulateur`), et il en cite les chiffres sans les recalculer.

Statuts d'un chiffre : `observe` (mesuré), `declare` (saisi dans la fiche), `suppose`
(hypothèse faute de donnée), `calcule` (dérivé par un moteur).
"""

import math
from datetime import date, datetime

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


def _fr_int(n) -> str:
    """9000 -> « 9 000 » (espace insécable fine absente des polices de base : espace simple)."""
    return f"{int(round(n)):,}".replace(",", " ")


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
        texte, date_source = ref.SOURCES[source]
        self.hypotheses[cle] = {"cle": cle, "valeur": valeur, "source": texte, "date": date_source}

    def hyp_fiche(self, cle: str, valeur: str):
        """Une hypothèse qui tient à la fiche elle-même (valeur par défaut, lecture d'un champ).
        Ce sont celles que le PDF affiche en clair sous « Hypothèses utilisées »."""
        self.hypotheses[cle] = {"cle": cle, "valeur": valeur, "source": "Fiche Maison", "date": None}


# --- Lecture de la fiche --------------------------------------------------------------------

def zone_climatique(code_postal: str | None) -> tuple[str, bool]:
    """Zone H1/H2/H3 du département, et si elle a été SUPPOSÉE (code postal illisible)."""
    dep = departement_du_code_postal(code_postal or "")
    if dep in ref.ZONE_CLIMATIQUE:
        return ref.ZONE_CLIMATIQUE[dep], False
    return settings.audit_zone_defaut, True


def _age(annee: int | None, aujourd_hui: date) -> int | None:
    if not annee or annee > aujourd_hui.year:
        return None
    return aujourd_hui.year - annee


def _profil(house: House, t: _Trace, aujourd_hui: date) -> dict:
    """Valeurs de la fiche utilisées par le moteur, avec leurs hypothèses quand elles manquent."""
    surface = house.surface_habitable or 0
    t.entree("surface_habitable", house.surface_habitable, "inconnue → aucun chiffrage au m²")
    if not surface:
        t.alertes.append("Surface habitable inconnue : les postes chiffrés au m² ne peuvent pas l'être.")

    niveaux = house.nb_niveaux or 1
    t.entree("nb_niveaux", house.nb_niveaux, "inconnu → 1 niveau (combles et plancher = surface habitable)")
    if not house.nb_niveaux:
        t.hyp_fiche("nb_niveaux", "1 niveau (valeur par défaut) : combles et plancher = surface habitable")

    occupants = house.nb_occupants if house.nb_occupants is not None else settings.audit_occupants_defaut
    t.entree("nb_occupants", house.nb_occupants, f"inconnu → {settings.audit_occupants_defaut} occupants")
    if house.nb_occupants is None:
        t.hyp_fiche("nb_occupants", f"{settings.audit_occupants_defaut} occupants (valeur par défaut)")

    zone, zone_supposee = zone_climatique(house.code_postal)
    t.entree("code_postal", house.code_postal)
    t.hyp("zone_climatique", zone + (" (supposée)" if zone_supposee else ""), "zone_climatique")

    chauffage = house.chauffage_principal or ref.CHAUFFAGE_DEFAUT
    t.entree("chauffage_principal", house.chauffage_principal,
             f"inconnu → {ref.CHAUFFAGE_DEFAUT} (cas le plus courant)")
    if not house.chauffage_principal:
        t.hyp_fiche("chauffage_principal", "chauffage électrique direct (valeur par défaut)")
    energie = ref.ENERGIE_CHAUFFAGE[chauffage]
    if chauffage == "autre":
        t.hyp_fiche("energie_chauffage_autre", "chauffage « autre » traité comme électrique")

    ecs = house.ecs or settings.audit_ecs_defaut
    t.entree("ecs", house.ecs, f"inconnue → {settings.audit_ecs_defaut}")
    if not house.ecs:
        t.hyp_fiche("ecs", "ballon électrique (valeur par défaut)")

    clim_pieces = 0
    if house.clim:
        if house.clim_nb_pieces is not None:
            clim_pieces = house.clim_nb_pieces
        else:
            clim_pieces = settings.audit_clim_pieces_defaut
            t.hyp_fiche("clim_nb_pieces", f"{clim_pieces} pièce climatisée (valeur par défaut)")
    if chauffage == "PAC_air_air":
        if house.clim:
            t.hyp_fiche("clim_pac_reversible",
                        "clim assurée par la PAC air/air réversible : comptée une seule fois")
        else:
            t.hyp_fiche("pac_air_air_ete",
                        "rafraîchissement d'été possible non compté, chauffage peut-être surestimé")
    if energie == "electricite" and house.chauffage_appoint in ref.APPOINT_HORS_FACTURE:
        t.hyp_fiche("appoint_hors_facture", "une partie du chauffage peut venir de l'appoint et "
                                            "n'apparaît pas dans la facture électrique")

    kva = int(house.puissance_souscrite) if house.puissance_souscrite else settings.audit_puissance_kva_defaut
    t.entree("puissance_souscrite", house.puissance_souscrite,
             f"inconnue → {settings.audit_puissance_kva_defaut} kVA")

    for champ in ("type_logement", "statut", "annee_construction", "dpe_lettre", "isolation_combles",
                  "isolation_murs", "isolation_plancher", "menuiseries", "ventilation", "regulation",
                  "chauffage_principal_annee", "chauffage_appoint", "chauffage_appoint_annee", "ecs_annee",
                  "clim", "clim_nb_pieces", "conso_elec_kwh_an", "objectifs"):
        t.entree(champ, getattr(house, champ))

    return {"surface": surface, "niveaux": niveaux, "occupants": occupants, "zone": zone,
            "zone_supposee": zone_supposee, "chauffage": chauffage, "energie": energie,
            "ecs": ecs, "kva": kva, "clim_pieces": clim_pieces, "aujourd_hui": aujourd_hui}


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
    """Électricité hors chauffage : mêmes couches que le simulateur (`simu_conso_*`).

    La climatisation n'est comptée qu'une fois, même quand c'est la PAC air/air réversible
    qui la fait : c'est le même appareil."""
    occ = max(p["occupants"], 1)
    base = settings.simu_conso_base_fixe_kwh_an + settings.simu_conso_base_par_occupant_kwh_an * occ
    ecs = _grille(settings.simu_conso_ecs_kwh_occupant_an, p["ecs"]) * occ
    clim = settings.simu_conso_clim_kwh_piece_an * p["clim_pieces"]
    t.hyp("usages_specifiques_kwh_an",
          {"base": round(base), "eau_chaude": round(ecs), "climatisation": round(clim)}, "usages_specifiques")
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
                f"Incohérence : une fois retirés les usages courants (~{_fr_int(usages)} kWh), la "
                f"consommation déclarée ({_fr_int(house.conso_elec_kwh_an)} kWh) ne laisse presque rien "
                "pour le chauffage. Les économies sont calculées sur l'estimation, à confirmer avec vos factures."
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


# --- Conseils sans chiffre ------------------------------------------------------------------

def economie_remplacement_pac(c: dict, t: _Trace) -> dict | None:
    """Ce qu'une PAC air/air neuve ferait gagner sur le chauffage d'aujourd'hui, à prix égal.

    Un conseil, pas une action : le remplacement viendra de toute façon, on ne le présente
    pas comme un investissement — ni coût, ni temps de retour, hors synthèse."""
    conso = c.get("conso_chauffage_retenue_kwh_an")
    if not conso:
        return None
    actuel = _grille(settings.audit_rendement_chauffage, "PAC_air_air")
    neuf = settings.audit_scop_pac_air_air_neuf
    t.hyp("scop_pac_air_air_neuf", neuf, "scop_air_air_neuf")
    eur = conso * (1 - actuel / neuf) * c["prix_energie_eur_kwh"]
    if eur <= 0:
        return None
    f = _fourchette(eur)
    return {"bas": f["bas"], "haut": f["haut"]}


def conseils_equipements(house: House, p: dict, t: _Trace, c: dict) -> list[dict]:
    """Un conseil par équipement qui a atteint `audit_age_alerte_pct` % de sa durée de vie."""
    vie_chauffage = dict(settings.audit_duree_vie_chauffage)
    vie_ecs = dict(settings.audit_duree_vie_ecs)
    candidats = (
        (house.chauffage_principal, house.chauffage_principal_annee, vie_chauffage),
        (house.chauffage_appoint, house.chauffage_appoint_annee, vie_chauffage),
        (house.ecs, house.ecs_annee, vie_ecs),
    )
    conseils = []
    for equipement, annee, table in candidats:
        age = _age(annee, p["aujourd_hui"])
        if equipement not in table or age is None:
            continue
        if age < table[equipement] * settings.audit_age_alerte_pct / 100:
            continue
        nom, pronom = ref.NOM_EQUIPEMENT[equipement]
        texte = ref.CONSEIL_AGE.format(equipement=nom, pronom=pronom, age=age)
        conseil = {"equipement": equipement, "age_ans": age, "duree_vie_ans": table[equipement]}
        eco = (economie_remplacement_pac(c, t)
               if equipement == "PAC_air_air" and annee == house.chauffage_principal_annee
               and equipement == house.chauffage_principal else None)
        if eco:
            texte += ref.CONSEIL_AGE_PAC_ECONOMIE.format(bas=_fr_int(eco["bas"]), haut=_fr_int(eco["haut"]))
            conseil.update({"economie_au_remplacement_eur": eco, "statut": "calcule"})
        elif equipement.startswith("PAC"):
            texte += ref.CONSEIL_AGE_PAC
        conseils.append({**conseil, "texte": texte})
    if conseils:
        t.hyp("duree_vie_equipements", {e["equipement"]: e["duree_vie_ans"] for e in conseils}, "equipements")
    return conseils


def _geste_applicable(g: dict, house: House, p: dict) -> bool:
    if g.get("si_chauffage") is not None and p["chauffage"] not in g["si_chauffage"]:
        return False
    if p["chauffage"] in g.get("sauf_chauffage", ()):
        return False
    if g.get("si_ecs") is not None and house.ecs not in g["si_ecs"]:
        return False  # eau chaude déclarée seulement : pas de geste sur un ballon supposé
    if g.get("si_clim") and not house.clim:
        return False
    return True


def gestes_gratuits(house: House, p: dict) -> list[dict]:
    gestes = [{"cle": g["cle"], "texte": g["texte"]} for g in ref.GESTES_GRATUITS if _geste_applicable(g, house, p)]
    return gestes[:ref.GESTES_MAX]


def confort_ete(house: House, p: dict, actions: list[dict]) -> dict | None:
    if p["zone"] not in ref.ZONES_CONFORT_ETE:
        return None
    combles = next((a for a in actions if a["action"] == "isolation_combles"), None)
    note = ref.CONFORT_ETE_COMBLES if combles and combles["horizon"] == "a_l_occasion" else None
    return {"conseils": list(ref.CONFORT_ETE), "note_combles": note,
            "note_clim": ref.CONFORT_ETE_CLIM_EXISTANTE if house.clim else None}


# --- Solaire --------------------------------------------------------------------------------

def resume_etude_simulateur(etude) -> dict:
    """Ce que l'audit retient d'une étude `simulateur_studies`, recopié tel quel du résultat
    stocké. Appelé par la route : le moteur ne lit jamais la base lui-même."""
    r = etude.resultat or {}
    ind, inv = r.get("indicateurs") or {}, r.get("investissement") or {}
    cree = etude.created_at
    return {
        "date": cree.date().isoformat() if isinstance(cree, datetime) else str(cree)[:10],
        "version_moteur": etude.version_moteur,
        "option": etude.nom,
        "puissance_kwc": ind.get("puissance_kwc"),
        "investissement_eur": inv.get("total_eur"),
        "economie_1re_annee_eur": ind.get("economie_1re_annee_eur"),
        "temps_retour_ans": ind.get("temps_retour_ans"),
        "gain_net_25_ans_eur": ind.get("gain_net_25_ans_eur"),
        "autonomie_pct": ind.get("autonomie_pct"),
    }


def _mois_ecoules(depuis: date, aujourd_hui: date) -> int:
    return (aujourd_hui.year - depuis.year) * 12 + aujourd_hui.month - depuis.month - (aujourd_hui.day < depuis.day)


def _solaire(house: House, p: dict, etude: dict | None, t: _Trace) -> tuple[dict | None, dict | None]:
    """(bloc solaire, action chiffrée ou None). Sans étude : une piste SANS AUCUN chiffre."""
    if etude:
        jour = date.fromisoformat(etude["date"])
        a_jour = _mois_ecoules(jour, p["aujourd_hui"]) <= settings.audit_etude_simulateur_max_mois
        source = f"simulateur, étude du {jour.strftime('%d/%m/%Y')}, moteur {etude.get('version_moteur')}"
        bloc = {"type": "etude", "etude": etude, "source": source, "a_mettre_a_jour": not a_jour,
                "mention": None if a_jour else "étude à mettre à jour", "lien": ref.LIEN_SIMULATEUR}
        t.hyp_fiche("etude_simulateur", source)
        inv, eco = etude.get("investissement_eur"), etude.get("economie_1re_annee_eur")
        if inv is None or eco is None:
            return bloc, None
        s = ref.SOLAIRE
        action = {
            "action": s["action"], "label": s["label"], "poste": s["poste"], "part_deperdition_pct": None,
            "_type": "solaire",
            "quantite": {"valeur": etude.get("puissance_kwc"), "unite": "kWc"},
            "cout_eur": {"bas": round(inv), "haut": round(inv)},
            "aide_estimee_eur": {"bas": 0, "haut": 0}, "aides_statut": "sans_objet", "aide_note": None,
            "reste_a_charge_eur": {"bas": round(inv), "haut": round(inv)},
            # Cités, pas recalculés : pas de fourchette ±15 % sur un chiffre d'étude.
            "economie_annuelle_eur": {"bas": round(eco), "haut": round(eco), "central": round(eco)},
            "temps_retour_ans": etude.get("temps_retour_ans"),
            "gain_pct_chauffage": None, "duree_vie_ans": s["duree_vie_ans"],
            "libelle_occasion": s["libelle_occasion"], "priorite_hierarchie": s["priorite_hierarchie"],
            "source": source, "mention": bloc["mention"],
            "statuts": {"cout_eur": "calcule", "economie_annuelle_eur": "calcule", "temps_retour_ans": "calcule"},
        }
        return bloc, action

    eligible = (house.type_logement == "maison" and house.statut in (None, "proprietaire")
                and (house.conso_elec_kwh_an or 0) >= settings.audit_solaire_conso_min_kwh)
    if not eligible:
        return None, None
    texte = ref.PISTE_SOLAIRE.format(conso=_fr_int(house.conso_elec_kwh_an))
    return {"type": "piste", "texte": texte, "lien": ref.LIEN_SIMULATEUR}, None


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
        return chauffage in ref.CHAUFFAGE_A_REMPLACER - ref.CHAUFFAGE_VERS_AIR_AIR
    if key == "pac_air_air":
        return chauffage in ref.CHAUFFAGE_VERS_AIR_AIR
    if key == "regulation":
        # Régulation non renseignée : supposée absente (hypothèse prudente, déjà v1).
        return ref.REGULATION_A_AMELIORER[house.regulation or "aucune"]
    if key == "ballon_thermodynamique":
        return house.ecs == "ballon_elec"  # déclaré : on ne remplace pas un ballon supposé
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
    if unit == "unite_air_air":
        n = math.ceil(surface / settings.audit_m2_par_unite_air_air) if surface else 1
        return min(max(1, n), settings.audit_unites_air_air_max), "unité(s) intérieure(s)"
    return 1, "forfait"


def _aide(a: dict, qte: float, cout_central: float) -> dict:
    forme, bas, haut = a["aide"]
    if forme == "pct":
        return {"bas": round(cout_central * bas), "haut": round(cout_central * haut)}
    if forme == "eur_m2":
        return {"bas": round(qte * bas), "haut": round(qte * haut)}
    return {"bas": bas, "haut": haut}


def _ballon(house: House, p: dict, t: _Trace) -> dict:
    """Coût et économie du ballon thermodynamique : surcoût si l'ancien est en fin de vie."""
    vie = _grille(settings.audit_duree_vie_ecs, "ballon_elec")
    age = _age(house.ecs_annee, p["aujourd_hui"])
    fin_de_vie = age is not None and age >= vie * settings.audit_age_alerte_pct / 100
    bas, haut = settings.audit_ballon_thermo_surcout_eur if fin_de_vie else settings.audit_ballon_thermo_cout_eur
    ecs = dict(settings.simu_conso_ecs_kwh_occupant_an)
    kwh = (ecs["ballon_elec"] - ecs["thermodynamique"]) * max(p["occupants"], 1)
    eur = kwh * prix_energie("electricite", p["kva"])
    t.hyp("ballon_thermodynamique", {"cout_eur": list(settings.audit_ballon_thermo_cout_eur),
                                     "surcout_eur": list(settings.audit_ballon_thermo_surcout_eur),
                                     "base_retenue": "surcout" if fin_de_vie else "cout_complet"}, "ballon_thermo")
    return {"cout": (bas, haut), "fin_de_vie": fin_de_vie, "kwh": kwh, "eur": eur}


def _actions_candidates(house: House, p: dict, deps: list[dict], t: _Trace) -> list[dict]:
    part_par_poste = {d["poste"]: d["part_pct"] for d in deps}
    actions = []
    for key, a in ref.ACTIONS.items():
        if not _action_recommandee(key, house, p["chauffage"]):
            continue
        qte, unite = _quantite(a, p)
        extra = {}
        if key == "ballon_thermodynamique":
            b = _ballon(house, p, t)
            cout_bas, cout_haut = b["cout"]
            unit_bas, unit_haut = b["cout"]
            extra = {"_type": "eau_chaude", "_eco_kwh": b["kwh"], "_eco_eur": b["eur"],
                     "base_cout": "surcout" if b["fin_de_vie"] else "cout_complet",
                     "contexte": a["libelle_fin_de_vie"] if b["fin_de_vie"] else None}
        else:
            if key == "pac_air_air":
                unit_bas, unit_haut = settings.audit_pac_air_air_cout_unite_eur
                extra = {"contexte": ref.TEXTES_ACTIONS[key]["note_convecteurs"]}
            else:
                unit_bas, unit_haut = a["cout_bas"], a["cout_haut"]
            cout_bas, cout_haut = round(unit_bas * qte), round(unit_haut * qte)
        central = (cout_bas + cout_haut) / 2
        aide = _aide(a, qte, central)
        actions.append({
            "action": key,
            "label": a["label"],
            "poste": a["poste"],
            "part_deperdition_pct": part_par_poste.get(a["poste"]),
            "quantite": {"valeur": qte, "unite": unite},
            "cout_unitaire_eur": {"bas": unit_bas, "haut": unit_haut, "unite": unite},
            "cout_eur": {"bas": cout_bas, "haut": cout_haut},
            "aide_estimee_eur": aide,
            # Mêmes unités que la colonne Coût : du plus favorable au moins favorable.
            "reste_a_charge_eur": {"bas": max(0, cout_bas - aide["haut"]), "haut": cout_haut - aide["bas"]},
            "aides_statut": "base_connaissances" if a.get("aide_source") else "a_verifier",
            "aide_source": a.get("aide_source"),
            "aide_note": a.get("aide_note"),
            "_reste_central": max(0.0, central - (aide["bas"] + aide["haut"]) / 2),
            "gain_pct_chauffage": (round(_gain_local(key, house), 3)
                                   if key not in ("pac_air_eau", "pac_air_air", "ballon_thermodynamique")
                                   else None),
            "duree_vie_ans": a["duree_vie_ans"],
            "libelle_occasion": a["libelle_occasion"],
            "priorite_hierarchie": a["priorite_hierarchie"],
            "statuts": {
                "quantite": "suppose", "cout_eur": "suppose", "aide_estimee_eur": "suppose",
                "economie_annuelle_eur": "calcule", "temps_retour_ans": "calcule",
                "part_deperdition_pct": next((d["statut"] for d in deps if d["poste"] == a["poste"]), None),
            },
            **extra,
        })
    if actions:
        t.hyp("couts_actions", {a["action"]: [a["cout_unitaire_eur"]["bas"], a["cout_unitaire_eur"]["haut"],
                                              a["cout_unitaire_eur"]["unite"]] for a in actions}, "couts_actions")
        t.hyp("aides", {x["action"]: list(ref.ACTIONS[x["action"]]["aide"]) for x in actions}, "aides")
        t.hyp("gains_pct_chauffage", {a["action"]: a["gain_pct_chauffage"] for a in actions
                                      if a["gain_pct_chauffage"] is not None}, "gains_actions")
        if any(a["action"] == "isolation_murs" for a in actions):
            t.hyp(f"ratio_murs[{p['niveaux']} niveau(x)]", ratio_murs(p["niveaux"]), "ratio_murs")
    return actions


def _appliquer(ordre: list[dict], conso: float, energie: str, prix: float, chauffage: str, kva: int) -> float:
    """Combinaison séquentielle : chaque action de CHAUFFAGE porte sur ce qui reste après les
    précédentes. L'eau chaude et le solaire ne touchent pas à cette consommation : leur
    économie est fixe, et s'additionne à part dans la synthèse.

    Renvoie le coût annuel du chauffage une fois tout le plan réalisé.
    """
    rendement = _grille(settings.audit_rendement_chauffage, chauffage)
    scops = {"pac_air_eau": _grille(settings.audit_rendement_chauffage, "PAC_air_eau"),
             "pac_air_air": _grille(settings.audit_rendement_chauffage, "PAC_air_air")}
    prix_elec = prix_energie("electricite", kva)
    for a in ordre:
        if a.get("_type") == "solaire":
            continue  # chiffres cités de l'étude, déjà posés
        if a.get("_type") == "eau_chaude":
            eur = a["_eco_eur"]
            a["economie_annuelle_kwh"] = round(a["_eco_kwh"])
            a["energie_economisee"] = "electricite"
        elif a["action"] in scops:
            scop = scops[a["action"]]
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


def raison_occasion(a: dict, c: dict) -> str:
    """Pourquoi une action finit « à l'occasion » — le texte affiché en dépend.

    - `apres_autres` : seule, elle serait prioritaire ; ce sont les actions placées avant
      elle qui ont pris le gain ;
    - `chauffage_peu_cher` : la chaleur coûte peu (`audit_chauffage_peu_cher_eur`) ;
    - `trop_cher` : même avec un chauffage cher, le prix des travaux dépasse ce qu'ils rapportent.
    """
    if a.get("_prioritaire_seule"):
        return "apres_autres"
    if c["cout_chauffage_actuel_eur"] <= settings.audit_chauffage_peu_cher_eur:
        return "chauffage_peu_cher"
    return "trop_cher"


def planifier(actions: list[dict], c: dict, p: dict, objectifs: list[str] | None) -> float:
    """Classe les actions (horizon → hiérarchie → critère secondaire) et les chiffre en séquence.

    Horizon et économies marginales dépendent l'un de l'autre : on itère. Une action passée
    « à l'occasion » y reste — son économie ne peut que baisser en reculant dans le plan —
    donc les horizons se stabilisent en au plus n tours ; la borne large ne sert qu'à
    l'objectif « facture », où l'ordre suit le temps de retour. Renvoie le coût final du
    chauffage. La hiérarchie (production = 4) garantit que le solaire ne passe jamais devant
    une action de sobriété ou d'enveloppe du même horizon.
    """
    facture = _objectif_facture(objectifs)
    etat = (c["conso_chauffage_retenue_kwh_an"], c["energie_chauffage"], c["prix_energie_eur_kwh"],
            p["chauffage"], p["kva"])

    def cle(a: dict):
        retour = a["temps_retour_ans"] if a["temps_retour_ans"] is not None else 99
        secondaire = retour if facture else -(a.get("part_deperdition_pct") or 0)
        return (ref.HORIZONS.index(a["horizon"]), a["priorite_hierarchie"], secondaire)

    # Premier passage : chaque action seule, sur la maison actuelle. On garde ce qu'elle
    # vaudrait seule : c'est ce qui dira pourquoi elle finit « à l'occasion ».
    for a in actions:
        _appliquer([a], *etat)
        retour = a["temps_retour_ans"]
        a["_prioritaire_seule"] = (retour is not None and retour <= settings.audit_horizon_retour_max_ans
                                   and retour <= a["duree_vie_ans"])
    occasion: set[str] = set()
    ordre, signature = actions, None
    cout_final = etat[0] * etat[2]
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
    for a in actions:
        if a["horizon"] == "a_l_occasion" and a.get("_type") not in ("eau_chaude", "solaire"):
            a["raison_occasion"] = raison_occasion(a, c)
    for i, a in enumerate(actions, 1):
        a["rang"] = i
        for interne in ("_reste_central", "_eco_kwh", "_eco_eur", "_prioritaire_seule"):
            a.pop(interne, None)
        if a["horizon"] != "a_l_occasion":
            a["libelle_occasion"] = None
    return cout_final


# --- Textes des fiches (v2.4) ---------------------------------------------------------------

def _remplir(texte: str | None, variables: dict) -> str | None:
    """Remplit les {variables} d'un texte de fiche. Une variable inconnue ou vide : None, la
    phrase ne s'affiche pas (jamais de texte inventé pour combler)."""
    if not texte:
        return None
    try:
        return texte.format_map({k: v for k, v in variables.items() if v is not None})
    except KeyError:
        return None


def variables_textes(house: House, p: dict, c: dict) -> dict:
    """Les valeurs que les textes des fiches peuvent citer, toutes tirées du calcul ou de la fiche."""
    kva = house.puissance_souscrite
    return {
        "chauffage": ref.ARTICLE_CHAUFFAGE.get(p["chauffage"]),
        "zone": ref.LIBELLE_ZONE.get(p["zone"]),
        "cout_chauffage": _fr_int(round(c["cout_chauffage_actuel_eur"], -1)),
        "age": _age(house.ecs_annee, p["aujourd_hui"]),
        "kva": int(kva) if kva else None,
        "mois": house.tarif_bloque_mois_restants,
        "dpe": (house.dpe_lettre or "").upper() or None,
    }


def _pourquoi(a: dict, textes: dict, variables: dict, avec_etude: bool, chauffage: str) -> str | None:
    if a["action"] == "ballon_thermodynamique":
        cle = "pourquoi_au_remplacement" if a.get("base_cout") == "surcout" else "pourquoi_sinon"
        phrases = [_remplir(textes.get(cle), variables)]
        if avec_etude:
            phrases.append(textes.get("avec_solaire"))
    else:
        cle = "pourquoi_peu_rentable" if a["horizon"] == "a_l_occasion" else "pourquoi_rentable"
        phrases = [_remplir(textes.get(cle), variables)]
        if a["action"] == "pac_air_eau" and chauffage == "elec_direct":
            phrases.append(textes.get("note_convecteurs"))
    phrases = [x for x in phrases if x]
    return " ".join(phrases) or None


def textes_actions(actions: list[dict], variables: dict, avec_etude: bool, chauffage: str):
    """Pose sur chaque action le « pourquoi » et les listes de sa fiche — des textes, aucun
    chiffre ajouté. Une action sans fiche (le solaire, cité d'une étude) n'en reçoit pas."""
    for a in actions:
        textes = ref.TEXTES_ACTIONS.get(a["action"])
        if not textes:
            continue
        a["pourquoi"] = _pourquoi(a, textes, variables, avec_etude, chauffage)
        for cle in ref.TEXTES_LISTES:
            a[cle] = list(textes.get(cle, ()))
        a["fiche"] = textes["fiche"]
        a["fiche_question"] = textes["question"]


def leviers_contrat(house: House, p: dict, variables: dict, avec_etude: bool) -> list[dict]:
    """Les leviers du contrat d'électricité, déclenchés par les seuls champs RENSEIGNÉS de la
    fiche. Une invitation à vérifier, jamais une affirmation, et sans chiffre."""
    habituel = _grille(settings.audit_kva_habituel,
                       "electrique" if p["energie"] == "electricite" else "non_electrique")
    ballon = house.ecs == "ballon_elec"
    declencheurs = {
        "puissance_a_verifier": bool(house.puissance_souscrite) and int(house.puissance_souscrite) > habituel,
        "hphc_ballon": house.option_tarifaire == "HPHC" and ballon,
        "base_avec_ballon": house.option_tarifaire == "base" and ballon and not avec_etude,
        "tarif_bloque_fin": (house.tarif_bloque == "oui" and house.tarif_bloque_mois_restants is not None
                             and house.tarif_bloque_mois_restants <= settings.audit_tarif_bloque_alerte_mois),
    }
    leviers = []
    for cle, actif in declencheurs.items():
        texte = _remplir(ref.LEVIERS_CONTRAT[cle], variables) if actif else None
        if texte:
            leviers.append({"cle": cle, "texte": texte})
    return leviers


def dpe_attestation(house: House, variables: dict) -> dict | None:
    """DPE d'avant 2026 et chauffage électrique : l'attestation mise à jour peut changer la
    lettre. Celle qu'elle afficherait n'est pas connue, et n'est donc jamais donnée."""
    if (variables["dpe"] and house.dpe_annee and house.dpe_annee < ref.DPE_REFORME_ANNEE
            and house.chauffage_principal in ref.CHAUFFAGES_ELECTRIQUES):
        return {"texte": ref.DPE_ELECTRIQUE_2026, "fiche": ref.FICHE_DPE}
    return None


def renovation_ampleur(house: House, p: dict, variables: dict) -> dict | None:
    """Maison E, F ou G (déclaré) avec au moins deux postes d'isolation à traiter : la piste
    de la rénovation d'ampleur, sans aucun chiffre (il relève de l'audit réglementaire)."""
    a_traiter = sum(getattr(house, champ) in etats for champ, etats in ref.AMPLEUR_POSTES_A_TRAITER)
    if (house.type_logement != "maison" or variables["dpe"] not in ref.DPE_AMPLEUR
            or a_traiter < ref.AMPLEUR_POSTES_MIN or house.statut not in (None, "proprietaire")):
        return None
    return {"texte": _remplir(ref.PISTE_AMPLEUR, variables), "vigilance": list(ref.VIGILANCE_AMPLEUR),
            "fossile": ref.FOSSILE_AMPLEUR if p["chauffage"] in ref.CHAUFFAGES_FOSSILES else None,
            "fiche": ref.FICHE_AMPLEUR}


# --- Climat et coût dans le temps (v2.4) ----------------------------------------------------

def eau_chaude_kwh(p: dict) -> float | None:
    """Électricité de l'eau chaude, la couche déjà utilisée pour les usages courants (réglages
    du simulateur). Une eau chaude au gaz n'y figure pas (0) : inconnue, rien n'est inventé."""
    kwh = _grille(settings.simu_conso_ecs_kwh_occupant_an, p["ecs"]) * max(p["occupants"], 1)
    return kwh or None


def _facteur_co2(energie: str, usage: str) -> float:
    facteurs = dict(settings.audit_facteurs_co2_kg_kwh)
    return facteurs[f"electricite_{usage}"] if energie == "electricite" else facteurs[energie]


def _dizaine(x: float) -> int:
    return int(round(x, -1))


def climat(c: dict, p: dict, actions: list[dict], t: _Trace) -> dict:
    """Émissions du chauffage et de l'eau chaude, aujourd'hui puis après le plan.

    Les actions sont déjà rangées et chiffrées : on rejoue leurs économies d'énergie dans
    l'ordre du plan. Une PAC change d'énergie : l'énergie retirée sort, l'électricité qu'elle
    consomme entre. La production solaire n'est pas comptée (ses chiffres sont ceux d'une
    étude, qui ne dit pas l'électricité réseau évitée)."""
    t.hyp("facteurs_co2_kg_kwh", dict(settings.audit_facteurs_co2_kg_kwh), "facteurs_co2")
    kwh, energie = float(c["conso_chauffage_retenue_kwh_an"]), c["energie_chauffage"]
    ecs = eau_chaude_kwh(p)

    def total() -> float:
        return kwh * _facteur_co2(energie, "chauffage") + (ecs or 0) * _facteur_co2("electricite", "eau_chaude")

    chauffage_kg = kwh * _facteur_co2(energie, "chauffage")
    eau_kg = ecs * _facteur_co2("electricite", "eau_chaude") if ecs else None
    apres_plan = None
    for a in actions:
        if apres_plan is None and a["horizon"] == "a_l_occasion":
            apres_plan = total()
        if a["categorie"] == "chauffage":
            if a.get("conso_apres_kwh_electricite") is not None:
                kwh, energie = float(a["conso_apres_kwh_electricite"]), "electricite"
            elif a.get("economie_annuelle_kwh"):
                kwh = max(0.0, kwh - a["economie_annuelle_kwh"])
        elif a["categorie"] == "eau_chaude" and ecs and a.get("economie_annuelle_kwh"):
            ecs = max(0.0, ecs - a["economie_annuelle_kwh"])
    tout = total()
    return {
        "chauffage_kg_an": _dizaine(chauffage_kg),
        "eau_chaude_kg_an": _dizaine(eau_kg) if eau_kg is not None else None,
        "apres_plan_recommande_kg_an": _dizaine(apres_plan if apres_plan is not None else tout),
        "apres_tout_le_plan_kg_an": _dizaine(tout),
        "facteurs": dict(settings.audit_facteurs_co2_kg_kwh),
        "statut": "calcule",
    }


def couts(c: dict, p: dict, plan: dict, t: _Trace) -> dict:
    """Chauffage et eau chaude sur 10 ans, à la hausse de prix du simulateur."""
    h = settings.simu_hausse_prix_kwh_pct_an
    t.hyp("hausse_prix_pct_an", h, "hausse_prix")
    facteur = sum((1 + h / 100) ** an for an in range(10))
    ecs = eau_chaude_kwh(p)
    eau = ecs * prix_energie("electricite", p["kva"]) if ecs else None
    chauffage = c["cout_chauffage_actuel_eur"]
    return {
        "chauffage_eur_an": chauffage,
        "eau_chaude_eur_an": round(eau) if eau is not None else None,
        "hausse_pct_an": h,
        "chauffage_et_eau_chaude_10_ans_eur": _dizaine((chauffage + (eau or 0)) * facteur),
        "economie_10_ans_plan_recommande_eur": _dizaine(plan["economie_annuelle_eur"]["central"] * facteur),
        "statut": "calcule",
    }


# --- Synthèse -------------------------------------------------------------------------------

def _decompte(nb: dict) -> str:
    morceaux = []
    if nb["maintenant"]:
        morceaux.append(f"{nb['maintenant']} action{'s' if nb['maintenant'] > 1 else ''} à faire maintenant")
    if nb["prioritaire"]:
        morceaux.append(f"{nb['prioritaire']} action{'s' if nb['prioritaire'] > 1 else ''} "
                        f"prioritaire{'s' if nb['prioritaire'] > 1 else ''}")
    if nb["a_l_occasion"]:
        morceaux.append(f"{nb['a_l_occasion']} à prévoir à l'occasion")
    return ", ".join(morceaux) if morceaux else "Aucune action chiffrée"


def _premiere_etape(actions: list[dict], solaire: dict | None, gestes: list[dict]) -> tuple[str, str]:
    """Jamais vide : une action utile, à défaut la piste solaire, à défaut un geste gratuit."""
    for a in actions:
        if a["horizon"] in ("maintenant", "prioritaire"):
            return a["label"], "action"
    if solaire and solaire["type"] == "piste":
        return ref.PISTE_SOLAIRE_COURTE, "piste_solaire"
    return gestes[0]["texte"], "geste"


def _message_sans_isolation(actions: list[dict], solaire: dict | None, cout_chauffage: float) -> str | None:
    isolations = [a for a in actions if a["action"] in ref.POSTES_ISOLATION]
    if not isolations or any(a["horizon"] != "a_l_occasion" for a in isolations):
        return None
    leviers = [a["label"].lower() for a in actions
               if a["action"] not in ref.POSTES_ISOLATION and a["horizon"] in ("maintenant", "prioritaire")]
    if solaire:
        leviers.append("étudier une production solaire")
    leviers.append("les gestes gratuits")
    return ref.MESSAGE_SANS_ISOLATION.format(cout=_fr_int(cout_chauffage), leviers=", ".join(leviers))


def _bloc_plan(actions: list[dict]) -> dict:
    """Totaux d'un groupe d'actions chiffrées (hors production solaire).

    Les économies sont la somme des économies MARGINALES du groupe : le plan recommandé
    précède toujours les actions « à l'occasion », donc son économie ne dépend pas d'elles,
    et les deux blocs ensemble redonnent les totaux de la synthèse. Chauffage et eau chaude
    restent séparés, comme dans la synthèse.
    """
    def somme(cle: str) -> dict:
        return {"bas": sum(a[cle]["bas"] for a in actions), "haut": sum(a[cle]["haut"] for a in actions)}

    def eco(*categories: str) -> dict:
        # Somme des bornes, pas une nouvelle fourchette sur la somme : une action seule doit
        # afficher exactement les mêmes chiffres dans le plan et dans sa ligne.
        groupe = [a["economie_annuelle_eur"] for a in actions if a["categorie"] in categories]
        return {k: sum(e[k] for e in groupe) for k in ("bas", "haut", "central")}

    return {"nb": len(actions), "investissement_eur": somme("cout_eur"),
            "aides_estimees_eur": somme("aide_estimee_eur"), "reste_a_charge_eur": somme("reste_a_charge_eur"),
            "economie_chauffage_eur": eco("chauffage"), "economie_eau_chaude_eur": eco("eau_chaude"),
            # Chauffage + eau chaude : le chiffre de la carte « Le plan recommandé ». Calculé
            # ici pour que le document n'ait jamais à additionner lui-même.
            "economie_annuelle_eur": eco("chauffage", "eau_chaude")}


def champs_supposes(entrees: list[dict]) -> list[dict]:
    """Les valeurs SUPPOSÉES de la fiche, de la plus à la moins décisive (`CHAMPS_A_PRECISER`).

    Ne lit que `entrees` : le PDF s'en sert aussi pour sa page d'hypothèses, sans rien
    recalculer. Une valeur supposée vaut la valeur par défaut du réglage, d'où `settings`.
    """
    supposes = {e["champ"] for e in entrees if e["statut"] == "suppose"}
    if "dpe_lettre" not in supposes:
        # Avec un DPE déclaré, l'année de construction n'entre pas dans le calcul : la
        # demander ne rendrait pas le pré-audit plus précis.
        supposes.discard("annee_construction")
    valeurs = {"kva": settings.audit_puissance_kva_defaut, "occupants": settings.audit_occupants_defaut}
    return [{"champ": champ, "libelle": libelle, "hypothese": hypothese.format(**valeurs)}
            for champ, libelle, hypothese in ref.CHAMPS_A_PRECISER if champ in supposes]


def a_preciser(entrees: list[dict]) -> list[dict]:
    """Les 3 valeurs supposées qui pèsent le plus sur le résultat."""
    return champs_supposes(entrees)[:ref.A_PRECISER_MAX]


def run_audit(house: House, etude_simulateur: dict | None = None, aujourd_hui: date | None = None) -> dict:
    """Produit le JSON structuré complet du pré-audit (sans texte LLM — chiffres déterministes).

    `etude_simulateur` : résumé de la dernière étude du simulateur (`resume_etude_simulateur`),
    passé par la route ; ses chiffres sont cités tels quels.
    """
    aujourd_hui = aujourd_hui or date.today()
    t = _Trace()
    score = compute_score(house)
    p = _profil(house, t, aujourd_hui)
    c = consommation(house, p, t)
    dep = deperditions(house)
    t.hyp("deperditions_base", ref.DEPERDITION_BASE, "deperditions")
    actions = _actions_candidates(house, p, dep, t)
    solaire, action_solaire = _solaire(house, p, etude_simulateur, t)
    if action_solaire:
        actions.append(action_solaire)
    cout_final = planifier(actions, c, p, house.objectifs)
    t.hyp("horizons", {"cout_max_eur": settings.audit_horizon_cout_max_eur,
                       "retour_max_ans": settings.audit_horizon_retour_max_ans}, "horizons")
    t.hyp("incertitude", settings.audit_incertitude, "incertitude")

    gestes = gestes_gratuits(house, p)
    conseils = conseils_equipements(house, p, t, c)
    cout_actuel = c["conso_chauffage_retenue_kwh_an"] * c["prix_energie_eur_kwh"]
    eco_chauffage = cout_actuel - cout_final
    eco_eau = sum(a["economie_annuelle_eur"]["central"] for a in actions if a.get("_type") == "eau_chaude")
    eco_total = eco_chauffage + eco_eau
    travaux = [a for a in actions if a.get("_type") != "solaire"]  # le solaire a ses propres chiffres
    nb = {h: sum(a["horizon"] == h for a in actions) for h in ref.HORIZONS}
    premiere, premiere_type = _premiere_etape(actions, solaire, gestes)

    variables = variables_textes(house, p, c)
    textes_actions(actions, variables, etude_simulateur is not None, p["chauffage"])
    for a in actions:
        a["categorie"] = {"eau_chaude": "eau_chaude", "solaire": "production"}.get(a.pop("_type", None), "chauffage")
    plan = [a for a in travaux if a["horizon"] in ("maintenant", "prioritaire")]
    occasion = [a for a in travaux if a["horizon"] == "a_l_occasion"]
    bloc_plan = _bloc_plan(plan)
    bloc_climat = climat(c, p, travaux, t)
    bloc_couts = couts(c, p, bloc_plan, t)

    return {
        "version_helios": settings.audit_version,
        # Date du relevé des aides appliquées : le PDF l'affiche, et un audit stocké garde la
        # sienne même quand les barèmes changent.
        "aides_date_reference": settings.audit_aides_date_reference,
        "completeness_score": score,
        "niveau": niveau_for_score(score),
        "entrees": t.entrees,
        "deperditions": dep,
        "deperditions_statut": "suppose" if any(d["statut"] == "suppose" and d["poste"] != "ponts_thermiques"
                                                 for d in dep) else "calcule",
        "consommation": c,
        "priorites": actions,
        "gestes": gestes,
        "conseils_equipements": conseils,
        "confort_ete": confort_ete(house, p, actions),
        # v2.4 : sans chiffre — le contrat et le DPE dans « Maintenant », la rénovation
        # d'ampleur dans « Pour aller plus loin ».
        "contrat": leviers_contrat(house, p, variables, etude_simulateur is not None),
        "dpe_attestation": dpe_attestation(house, variables),
        "renovation_ampleur": renovation_ampleur(house, p, variables),
        "climat": bloc_climat,
        "couts": bloc_couts,
        "solaire": solaire,
        "synthese": {
            "nb_actions": len(actions),
            "nb_par_horizon": nb,
            "decompte": _decompte(nb),
            "investissement_eur": {"bas": sum(a["cout_eur"]["bas"] for a in travaux),
                                   "haut": sum(a["cout_eur"]["haut"] for a in travaux)},
            "aides_estimees_eur": {"bas": sum(a["aide_estimee_eur"]["bas"] for a in travaux),
                                   "haut": sum(a["aide_estimee_eur"]["haut"] for a in travaux)},
            "reste_a_charge_eur": {"bas": sum(a["reste_a_charge_eur"]["bas"] for a in travaux),
                                   "haut": sum(a["reste_a_charge_eur"]["haut"] for a in travaux)},
            "aides_statut": "a_verifier",
            "cout_chauffage_actuel_eur": round(cout_actuel),
            "economie_chauffage_eur": _fourchette(eco_chauffage) if eco_chauffage > 0 else None,
            "economie_eau_chaude_eur": _fourchette(eco_eau) if eco_eau > 0 else None,
            "economie_annuelle_totale_eur": _fourchette(eco_total) if eco_total > 0 else None,
            "economie_chauffage_pct": round(100 * eco_chauffage / cout_actuel) if cout_actuel else None,
            "premiere_action": premiere,
            "premiere_action_type": premiere_type,  # action | piste_solaire | geste
            "message_sans_isolation": _message_sans_isolation(actions, solaire, cout_actuel),
            # v2.3 : ce qui est recommandé, séparé de ce qui attend une occasion — le total
            # ci-dessus additionne les deux, ce qu'un lecteur prend pour le budget conseillé.
            "plan_recommande": bloc_plan,
            "a_l_occasion": _bloc_plan(occasion),
        },
        "a_preciser": a_preciser(t.entrees),
        "alertes": t.alertes,
        "hypotheses": list(t.hypotheses.values()),
        "avertissement": (
            "Pré-diagnostic indicatif (ordres de grandeur), ne remplace ni un DPE ni un audit "
            "énergétique réalisé par un professionnel certifié. Coûts, aides et économies à confirmer."
        ),
    }
