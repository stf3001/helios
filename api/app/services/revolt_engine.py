"""Moteur "Revolt" — simulateur avancé PV + batterie + tarifs, à consommation réelle égale.

Entièrement déterministe (aucun LLM, doc 07 §6) : prend en entrée deux séries horaires sur
un an (8760 points) — consommation du logement et production PV — et simule heure par heure
l'effet de différentes briques : ajout de panneaux seuls, ajout d'une batterie physique,
passage en stockage virtuel (MyLight), et/ou changement de tarif (fixe / SOBRY SoFlex /
SOBRY SoCap). Les courbes elles-mêmes (consommation, prix) peuvent être réelles ou simulées
selon les sources branchées (`enedis_client`, `sobry_tariffs`) — ce module ne le sait pas et
ne s'en préoccupe pas : il ne fait que le calcul, à partir de ce qu'on lui donne.
"""

from app.core.config import settings
from app.services import sobry_tariffs

Hourly = list[float]


def _import_export(conso_h: Hourly, prod_h: Hourly) -> tuple[Hourly, Hourly]:
    """Sans aucun stockage : import réseau et export surplus, heure par heure."""
    import_h = [max(0.0, c - p) for c, p in zip(conso_h, prod_h)]
    export_h = [max(0.0, p - c) for c, p in zip(conso_h, prod_h)]
    return import_h, export_h


def simulate_pv_only(conso_h: Hourly, prod_h: Hourly) -> dict:
    """PV seul, sans aucun stockage — autoconsommation directe uniquement."""
    import_h, export_h = _import_export(conso_h, prod_h)
    conso_annuelle = sum(conso_h)
    prod_annuelle = sum(prod_h)
    autoconso_directe = sum(min(c, p) for c, p in zip(conso_h, prod_h))
    return {
        "import_h": import_h,
        "export_h": export_h,
        "autoconso_directe_kwh": round(autoconso_directe),
        "import_reseau_kwh": round(sum(import_h)),
        "surplus_exporte_kwh": round(sum(export_h)),
        "taux_autoconsommation": round(autoconso_directe / prod_annuelle, 3) if prod_annuelle else 0.0,
        "taux_couverture_besoins": round(autoconso_directe / conso_annuelle, 3) if conso_annuelle else 0.0,
    }


def simulate_pv_battery(
    conso_h: Hourly, prod_h: Hourly, capacity_kwh: float, power_kw: float, efficiency: float | None = None
) -> dict:
    """PV + batterie physique — simulation glouton heure par heure (charge dès qu'il y a du
    surplus, décharge dès qu'il y a un besoin, dans la limite de la capacité et de la puissance
    de charge/décharge). Pertes appliquées à la charge (rendement aller-retour, doc 09 §1)."""
    eff = efficiency if efficiency is not None else settings.revolt_battery_efficiency
    soc = 0.0
    import_h: Hourly = []
    export_h: Hourly = []
    autoconso_directe = 0.0
    charge_totale = 0.0
    decharge_totale = 0.0

    for conso, prod in zip(conso_h, prod_h):
        direct = min(conso, prod)
        autoconso_directe += direct
        surplus = prod - direct
        reste_conso = conso - direct

        charge = min(surplus, power_kw, capacity_kwh - soc) if surplus > 0 else 0.0
        soc += charge * eff
        charge_totale += charge
        export_h.append(surplus - charge)

        decharge = min(reste_conso, power_kw, soc) if reste_conso > 0 else 0.0
        soc -= decharge
        decharge_totale += decharge
        import_h.append(reste_conso - decharge)

    conso_annuelle = sum(conso_h)
    prod_annuelle = sum(prod_h)
    autoconso_totale = autoconso_directe + decharge_totale
    return {
        "import_h": import_h,
        "export_h": export_h,
        "autoconso_directe_kwh": round(autoconso_directe),
        "restitue_batterie_kwh": round(decharge_totale),
        "autoconso_totale_kwh": round(autoconso_totale),
        "import_reseau_kwh": round(sum(import_h)),
        "surplus_exporte_kwh": round(sum(export_h)),
        "taux_autoconsommation": round(autoconso_totale / prod_annuelle, 3) if prod_annuelle else 0.0,
        "taux_couverture_besoins": round(autoconso_totale / conso_annuelle, 3) if conso_annuelle else 0.0,
    }


def simulate_mylight(conso_h: Hourly, prod_h: Hourly, power_kwc: float) -> dict:
    """PV + stockage virtuel MyLight ("MyBattery") — capacité illimitée : tout surplus est
    "mis de côté", récupérable ensuite à un tarif de restitution (TURPE + accise), moyennant
    un abonnement mensuel proportionnel à la puissance installée. Tarifs 2026 relevés
    publiquement (papernest.com, adsolar.fr) — à confirmer auprès de MyLight avant décision.
    Contrainte réelle et non négociable : nécessite de souscrire l'électricité chez le
    fournisseur mylight150."""
    soc = 0.0
    import_h: Hourly = []
    surplus_stocke_total = 0.0
    restitue_total = 0.0

    for conso, prod in zip(conso_h, prod_h):
        direct = min(conso, prod)
        surplus = prod - direct
        reste_conso = conso - direct

        soc += surplus
        surplus_stocke_total += surplus

        decharge = min(reste_conso, soc)
        soc -= decharge
        restitue_total += decharge
        import_h.append(reste_conso - decharge)

    return {
        "import_residuel_h": import_h,
        "surplus_stocke_kwh": round(surplus_stocke_total),
        "restitue_kwh": round(restitue_total),
        "solde_virtuel_fin_annee_kwh": round(soc),
        "frais_activation_unique_eur": settings.mylight_activation_eur,
        "abonnement_annuel_eur": round(power_kwc * settings.mylight_abonnement_eur_par_kwc_mois * 12, 2),
        "cout_restitution_eur": round(restitue_total * settings.mylight_restitution_eur_kwh, 2),
        "avertissement": (
            "Nécessite de souscrire l'électricité chez mylight150 (fournisseur alternatif) — "
            "à mettre en balance avec votre offre actuelle. Tarifs 2026 relevés publiquement, "
            "à confirmer auprès de MyLight avant toute décision."
        ),
    }


def cost_annuel(
    import_h: Hourly,
    export_h: Hourly,
    mode: str,
    prix_achat_fixe: float | None = None,
    prix_revente_fixe: float | None = None,
) -> float:
    """Coût net annuel (achats - revenus de revente), pour un mode tarifaire donné.

    mode="fixe" : prix constant (achat/revente), comme le simulateur solaire standard.
    mode="soflex"/"socap" : grille de test SOBRY horaire (`sobry_tariffs`) — le surplus est
    supposé revendu au même prix de marché que l'achat (simplification ; les offres réelles
    peuvent distinguer prix d'achat et tarif d'injection — à confirmer auprès de SOBRY).
    """
    if mode == "fixe":
        prix_achat = prix_achat_fixe if prix_achat_fixe is not None else settings.solar_prix_achat_eur_kwh
        prix_revente = prix_revente_fixe if prix_revente_fixe is not None else settings.solar_prix_revente_eur_kwh
        achat = sum(i * prix_achat for i in import_h)
        revente = sum(e * prix_revente for e in export_h)
    elif mode in ("soflex", "socap"):
        prix_h = sobry_tariffs.hourly_prices(mode)
        achat = sum(i * p for i, p in zip(import_h, prix_h))
        revente = sum(e * p for e, p in zip(export_h, prix_h))
    else:
        raise ValueError(f"Mode tarifaire inconnu : {mode}")
    return round(achat - revente, 2)


def compare_scenarios(
    conso_h: Hourly,
    prod_h: Hourly,
    *,
    battery_kwh: float | None = None,
    battery_power_kw: float | None = None,
    mylight_power_kwc: float | None = None,
    tarif_modes: tuple[str, ...] = ("fixe",),
) -> dict:
    """Compare, à consommation réelle égale, plusieurs combinaisons production/stockage ×
    tarif. Renvoie une liste de lignes {brique, tarif, cout_annuel_eur, economie_vs_actuel_*}."""
    lignes: list[dict] = []

    # Référence : situation actuelle, sans PV, au(x) tarif(s) demandé(s).
    zero_h = [0.0] * len(conso_h)
    couts_reference: dict[str, float] = {}
    for mode in tarif_modes:
        cout = cost_annuel(conso_h, zero_h, mode)
        couts_reference[mode] = cout
        lignes.append({"brique": "actuel_sans_pv", "tarif": mode, "cout_annuel_eur": cout,
                        "economie_vs_actuel_eur": 0.0, "economie_vs_actuel_pct": 0.0})

    def _ajouter(brique: str, import_h: Hourly, export_h: Hourly, extra_annuel: float = 0.0, **detail):
        for mode in tarif_modes:
            cout = cost_annuel(import_h, export_h, mode) + extra_annuel
            ref = couts_reference[mode]
            economie = ref - cout
            lignes.append({
                "brique": brique, "tarif": mode, "cout_annuel_eur": round(cout, 2),
                "economie_vs_actuel_eur": round(economie, 2),
                "economie_vs_actuel_pct": round(100 * economie / ref, 1) if ref else 0.0,
                **detail,
            })

    pv_seul = simulate_pv_only(conso_h, prod_h)
    _ajouter("pv_seul", pv_seul["import_h"], pv_seul["export_h"],
             taux_autoconsommation=pv_seul["taux_autoconsommation"],
             taux_couverture_besoins=pv_seul["taux_couverture_besoins"])

    if battery_kwh and battery_power_kw:
        pv_batt = simulate_pv_battery(conso_h, prod_h, battery_kwh, battery_power_kw)
        _ajouter("pv_batterie_physique", pv_batt["import_h"], pv_batt["export_h"],
                 taux_autoconsommation=pv_batt["taux_autoconsommation"],
                 taux_couverture_besoins=pv_batt["taux_couverture_besoins"])

    if mylight_power_kwc:
        my = simulate_mylight(conso_h, prod_h, mylight_power_kwc)
        extra = my["abonnement_annuel_eur"] + my["cout_restitution_eur"]
        _ajouter("pv_mylight_batterie_virtuelle", my["import_residuel_h"], zero_h, extra_annuel=extra,
                 frais_activation_unique_eur=my["frais_activation_unique_eur"],
                 avertissement=my["avertissement"])

    return {"lignes": lignes}
