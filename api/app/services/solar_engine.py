"""Moteur déterministe de scénarios solaires — doc 09 §1 étape 5.

RÈGLE PROJET (doc 07 §6) : ces chiffres viennent d'un calcul déterministe, JAMAIS du LLM,
et sont toujours présentés en fourchettes « à confirmer par un professionnel ». Toutes les
hypothèses économiques sont dans `config.py` (constantes calibrables, ordres de grandeur 2026).
"""

from app.core.config import settings

# Technologies de stockage comparées (ordres de grandeur 2026, À CONFIRMER au devis).
# Le stockage inertie (Energisto, partenaire) : ~10 kWh pour ~9000 € => ~900 €/kWh, garantie 40 ans.
STORAGE_TECHS = [
    {"tech": "lfp", "label": "Batterie lithium (LFP)", "cout_par_kwh_eur": 700, "garantie_ans": 10,
     "note": "Référence actuelle : compacte et fiable."},
    {"tech": "sodium", "label": "Batterie sodium-ion", "cout_par_kwh_eur": 600, "garantie_ans": 12,
     "note": "Émergente en 2026 : bon marché, excellente au froid, un peu plus volumineuse."},
    {"tech": "inertie", "label": "Stockage par inertie (Energisto)", "cout_par_kwh_eur": 900, "garantie_ans": 40,
     "note": "Mécanique, sans chimie : très longue durée de vie (garantie 40 ans)."},
]


def _fourchette(value: float) -> dict:
    demi = settings.solar_incertitude
    return {
        "bas": round(value * (1 - demi)),
        "haut": round(value * (1 + demi)),
        "central": round(value),
    }


def _scenario_for_power(power_kwc: int, annual_kwh: float, conso_kwh: int) -> dict:
    cout_installation = power_kwc * settings.solar_cout_par_kwc_eur

    profils = {}
    for nom, taux in (
        ("sans_pilotage", settings.solar_autoconso_sans_pilotage),
        ("avec_pilotage", settings.solar_autoconso_avec_pilotage),
    ):
        # l'autoconsommation ne peut pas dépasser la conso du foyer
        autoconso_kwh = min(annual_kwh * taux, conso_kwh)
        surplus_kwh = max(annual_kwh - autoconso_kwh, 0)
        economie = autoconso_kwh * settings.solar_prix_achat_eur_kwh + surplus_kwh * settings.solar_prix_revente_eur_kwh
        retour_ans = round(cout_installation / economie, 1) if economie > 0 else None
        profils[nom] = {
            "taux_autoconso_pct": round(100 * autoconso_kwh / annual_kwh) if annual_kwh else 0,
            "autoconso_kwh": round(autoconso_kwh),
            "surplus_kwh": round(surplus_kwh),
            "economie_annuelle_eur": _fourchette(economie),
            "temps_retour_ans": retour_ans,
        }

    # Comparaison des technologies de stockage (même gain d'autoconso, coûts/garanties différents)
    capacite_kwh = power_kwc  # dimensionnement grossier : ~1 kWh utile / kWc
    taux_stock = min(settings.solar_autoconso_avec_pilotage + settings.solar_gain_autoconso_batterie, 1.0)
    autoconso_stock = min(annual_kwh * taux_stock, conso_kwh)
    surplus_stock = max(annual_kwh - autoconso_stock, 0)
    economie_stock = (
        autoconso_stock * settings.solar_prix_achat_eur_kwh + surplus_stock * settings.solar_prix_revente_eur_kwh
    )
    stockage_options = []
    for tech in STORAGE_TECHS:
        cout_total = cout_installation + capacite_kwh * tech["cout_par_kwh_eur"]
        retour = round(cout_total / economie_stock, 1) if economie_stock > 0 else None
        stockage_options.append({
            "tech": tech["tech"],
            "label": tech["label"],
            "capacite_kwh": capacite_kwh,
            "taux_autoconso_pct": round(100 * autoconso_stock / annual_kwh) if annual_kwh else 0,
            "economie_annuelle_eur": _fourchette(economie_stock),
            "cout_total_eur": _fourchette(cout_total),
            "temps_retour_ans": retour,
            "garantie_ans": tech["garantie_ans"],
            "note": tech["note"],
        })

    return {
        "puissance_kwc": power_kwc,
        "production_annuelle_kwh": round(annual_kwh),
        "cout_installation_eur": _fourchette(cout_installation),
        "profils_autoconso": profils,
        "stockage_options": stockage_options,
    }


def build_scenarios(pvgis_result: dict, conso_kwh_an: int | None) -> dict:
    """Construit les scénarios économiques pour chaque puissance à partir de la production PVGIS."""
    conso = conso_kwh_an or settings.solar_conso_defaut_kwh_an
    by_power = pvgis_result["by_power"]
    return {
        "conso_reference_kwh": conso,
        "conso_estimee": conso_kwh_an is None,  # True si on a utilisé la valeur par défaut (mode public)
        "par_puissance": {
            power: _scenario_for_power(int(power), data["annual_kwh"], conso)
            for power, data in by_power.items()
        },
        "avertissement": (
            "Estimations indicatives (ordres de grandeur), ne remplacent pas une étude réalisée "
            "par un installateur certifié. Prix de l'énergie et coûts d'installation à confirmer."
        ),
    }
