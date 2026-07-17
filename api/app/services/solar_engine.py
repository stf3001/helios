"""Moteur déterministe de scénarios solaires — doc 09 §1 étape 5.

RÈGLE PROJET (doc 07 §6) : ces chiffres viennent d'un calcul déterministe, JAMAIS du LLM,
et sont toujours présentés en fourchettes « à confirmer par un professionnel ». Toutes les
hypothèses économiques sont dans `config.py` (constantes calibrables, ordres de grandeur 2026).
"""

from app.core.config import settings


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

    # Scénario batterie : gain d'autoconso sur le profil "avec pilotage"
    taux_batt = min(settings.solar_autoconso_avec_pilotage + settings.solar_gain_autoconso_batterie, 1.0)
    autoconso_batt = min(annual_kwh * taux_batt, conso_kwh)
    surplus_batt = max(annual_kwh - autoconso_batt, 0)
    economie_batt = (
        autoconso_batt * settings.solar_prix_achat_eur_kwh + surplus_batt * settings.solar_prix_revente_eur_kwh
    )
    capacite_batt_kwh = power_kwc  # dimensionnement grossier : ~1 kWh utile / kWc
    cout_batt = cout_installation + capacite_batt_kwh * settings.solar_cout_batterie_par_kwh_eur
    retour_batt = round(cout_batt / economie_batt, 1) if economie_batt > 0 else None

    return {
        "puissance_kwc": power_kwc,
        "production_annuelle_kwh": round(annual_kwh),
        "cout_installation_eur": _fourchette(cout_installation),
        "profils_autoconso": profils,
        "scenario_batterie": {
            "capacite_kwh": capacite_batt_kwh,
            "taux_autoconso_pct": round(100 * autoconso_batt / annual_kwh) if annual_kwh else 0,
            "economie_annuelle_eur": _fourchette(economie_batt),
            "cout_total_eur": _fourchette(cout_batt),
            "temps_retour_ans": retour_batt,
        },
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
