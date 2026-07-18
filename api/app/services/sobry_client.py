"""Client SOBRY — doc 09 §2.

Deux usages :
- `spot_prices()` : courbe de prix spot quart-horaire (API publique SOBRY si configurée,
  sinon courbe représentative de démonstration, clairement étiquetée).
- `estimation()` : estimation tarifaire à partir du profil (simulée tant que l'intégration
  réelle SOBRY — via PDL + consentement — n'est pas branchée).

Aucun appel réseau vers SOBRY n'est fait sans URL configurée ; l'intégration réelle
(transmission du PDL) nécessite le consentement explicite du client (géré côté router).
"""

import httpx

from app.core.config import settings
from app.models.house import House

# Profil de prix journalier représentatif (EUR/kWh TTC), 24 valeurs horaires — creux la nuit,
# pointe en soirée. Sert de démonstration quand l'API SOBRY n'est pas configurée.
_COURBE_DEMO = [
    0.11, 0.10, 0.10, 0.09, 0.09, 0.10, 0.13, 0.17,
    0.20, 0.19, 0.17, 0.16, 0.15, 0.14, 0.14, 0.15,
    0.18, 0.24, 0.29, 0.31, 0.27, 0.21, 0.16, 0.13,
]


async def spot_prices() -> dict:
    """Prix spot du jour. Renvoie {source, unite, pas, points:[{h, prix}]}."""
    if settings.sobry_spot_api_url:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(settings.sobry_spot_api_url)
                res.raise_for_status()
                data = res.json()
            return {"source": "sobry_api", "unite": "EUR/kWh", "pas": "quart_horaire", "points": data}
        except (httpx.HTTPError, ValueError):
            pass  # repli sur la courbe de démonstration

    points = [{"h": h, "prix": p} for h, p in enumerate(_COURBE_DEMO)]
    return {
        "source": "demo",  # étiquette claire : ce n'est pas un prix réel SOBRY
        "unite": "EUR/kWh",
        "pas": "horaire",
        "points": points,
        "note": "Courbe représentative (démonstration) — brancher l'API SOBRY pour les prix réels.",
    }


def estimation(house: House, pdl: str) -> dict:
    """Estimation tarifaire simulée à partir du profil (déterministe, à remplacer par l'API SOBRY réelle).

    Le gain estimé dépend de la « pilotabilité » du profil : plus le foyer peut déplacer ses usages,
    plus un tarif dynamique est avantageux. Chiffres = ordres de grandeur, jamais présentés comme certains.
    """
    from app.services.energy_advisor import advice

    compat = advice(house)["tarif_dynamique"]["compatibilite"]
    gain_pct = {"favorable": 12.0, "neutre": 4.0, "prudence": 1.0}.get(compat, 3.0)

    # Base de facture annuelle indicative pour exprimer le gain en euros
    conso = house.conso_elec_kwh_an or 4500
    facture_estimee = round(conso * settings.solar_prix_achat_eur_kwh)
    gain_eur = round(facture_estimee * gain_pct / 100)

    return {
        "pdl": pdl,
        "compatibilite": compat,
        "gain_estime_pct": gain_pct,
        "gain_estime_eur_an": gain_eur,
        "facture_reference_eur_an": facture_estimee,
        "offres": ["SoCap (plafond mensuel garanti)", "SoFlex (optimisation maximale)"],
        "source": "estimation_simulee",  # à remplacer par le retour réel SOBRY (courbe de charge PDL)
    }
