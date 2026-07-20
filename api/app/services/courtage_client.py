"""Courtage énergie — recueil d'infos → demande au partenaire courtier → résultat → avis Helios.

Même logique que le module SOBRY : tant que l'intégration réelle d'un courtier n'est pas
branchée, le résultat est simulé de façon déterministe à partir du profil du foyer.
Les chiffres sont des ordres de grandeur, jamais présentés comme certains.
"""
from app.core.config import settings
from app.models.house import House


def estimation(house: House | None = None, infos: dict | None = None, gain_pct: float | None = None) -> dict:
    """Estimation de courtage à partir des infos recueillies (fournisseur/offre/conso/puissance…).

    Utilisable pour un particulier (avec `house`) ou un pro (house=None, infos issues du profil pro).
    La facture de référence privilégie le montant déclaré, sinon la conso × prix. `profil_transmis`
    trace ce qui est envoyé au courtier.
    """
    infos = infos or {}
    conso = infos.get("conso_annuelle_kwh") or (house.conso_elec_kwh_an if house else None) or 4500
    facture = infos.get("montant_facture_annuelle_eur") or round(conso * settings.solar_prix_achat_eur_kwh)
    gain_pct = gain_pct if gain_pct is not None else settings.courtage_gain_estime_pct
    gain_eur = round(facture * gain_pct / 100)

    profil_transmis = {
        "fournisseur_actuel": infos.get("fournisseur_actuel"),
        "offre_actuelle": infos.get("offre_actuelle"),
        "conso_annuelle_kwh": conso,
        "puissance_kva": infos.get("puissance_kva") or (house.puissance_souscrite if house else None),
        "option_tarifaire": infos.get("option_tarifaire") or (house.option_tarifaire if house else None),
    }
    return {
        "offre_actuelle": infos.get("offre_actuelle"),
        "profil_transmis": profil_transmis,
        "facture_reference_eur_an": facture,
        "gain_estime_pct": gain_pct,
        "gain_estime_eur_an": gain_eur,
        "meilleures_offres": [
            "Offre à prix indexé (remise sur le TRV)",
            "Offre à prix fixe 2 ans",
        ],
        "source": "estimation_simulee",  # à remplacer par le retour réel du partenaire courtier
    }


def helios_opinion(estimation_result: dict) -> tuple[str, bool]:
    """Avis indépendant d'Helios (règle des 5 %). Renvoie (texte, favorable)."""
    gain = estimation_result["gain_estime_pct"]
    comparateur = settings.energie_comparateur_public
    if gain < settings.sobry_seuil_gain_pct:
        return (
            f"L'économie estimée (~{gain}%) est marginale : elle ne justifie pas de changer d'offre pour l'instant. "
            f"Restez sur votre contrat actuel et vérifiez librement sur le comparateur public {comparateur}.",
            False,
        )
    return (
        f"Un changement d'offre pourrait vous faire économiser environ {gain}% (~{estimation_result['gain_estime_eur_an']} EUR/an), "
        f"à confirmer sur votre profil réel. Ce n'est pas « la meilleure offre du marché » : comparez librement sur le "
        f"comparateur public indépendant {comparateur}. HELIOS ne touche jamais de commission de votre part.",
        True,
    )
