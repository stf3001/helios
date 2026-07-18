"""Conseil énergie niveau 1 — doc 09 §2 (sans tiers, gratuit, indépendant).

Analyse déterministe de la fiche : puissance souscrite adaptée ? option HP/HC pertinente ?
profil compatible avec un tarif dynamique (type SOBRY) ? Recommandations directes.
Aucun chiffre n'est produit par le LLM — ordres de grandeur calibrables ici.
"""

from app.models.house import House

# Usages électriques pilotables (déplaçables en heures creuses / vers les heures peu chères).
_ECS_PILOTABLE = {"ballon_elec", "thermodynamique"}
_CHAUFFAGE_ELEC = {"convecteurs_elec", "electrique", "pac", "pac_air_air", "pac_air_eau"}
_CHAUFFAGE_ELEC_NON_PILOTABLE = {"convecteurs_elec", "electrique"}

# Coût indicatif de l'abonnement par kVA et par an (€/kVA/an) — écart entre deux puissances.
_ABONNEMENT_EUR_KVA_AN = 14


def _puissance_kva(house: House) -> int | None:
    if not house.puissance_souscrite:
        return None
    try:
        return int(str(house.puissance_souscrite).replace("kVA", "").strip())
    except ValueError:
        return None


def _puissance_conseillee(house: House) -> int:
    """Puissance indicative selon surface, chauffage et occupants (ordre de grandeur)."""
    base = 6
    if house.chauffage_principal in _CHAUFFAGE_ELEC:
        base = 9
        if (house.surface_habitable or 0) > 100:
            base = 12
    if (house.surface_habitable or 0) > 150:
        base = max(base, 12)
    if house.clim:
        base = max(base, 9)
    return base


def _pilotables(house: House) -> list[str]:
    items = []
    if house.ecs in _ECS_PILOTABLE:
        items.append("ballon d'eau chaude électrique")
    if house.chauffage_principal in ("pac", "pac_air_eau", "pac_air_air"):
        items.append("pompe à chaleur")
    if house.orientation_toiture or house.surface_toit_exploitable:
        items.append("production solaire (autoconsommation)")
    return items


def advice(house: House) -> dict:
    """Renvoie les recommandations niveau 1 (liste) + une évaluation de compatibilité au tarif dynamique."""
    recos: list[dict] = []

    # 1. Puissance souscrite
    kva = _puissance_kva(house)
    conseillee = _puissance_conseillee(house)
    if kva is not None:
        if kva > conseillee:
            economie = (kva - conseillee) * _ABONNEMENT_EUR_KVA_AN
            recos.append({
                "sujet": "Puissance souscrite",
                "constat": f"Vous êtes en {kva} kVA ; {conseillee} kVA suffiraient probablement à votre usage.",
                "conseil": f"Vérifiez vos pics de consommation, puis envisagez de passer à {conseillee} kVA "
                           f"(économie indicative ~{economie} EUR/an sur l'abonnement, à confirmer).",
            })
        elif kva < conseillee:
            recos.append({
                "sujet": "Puissance souscrite",
                "constat": f"Vous êtes en {kva} kVA, ce qui peut être juste pour votre logement.",
                "conseil": f"Si vous constatez des coupures (disjonctions), {conseillee} kVA seraient plus confortables.",
            })
        else:
            recos.append({
                "sujet": "Puissance souscrite",
                "constat": f"Votre puissance ({kva} kVA) semble bien dimensionnée.",
                "conseil": "Rien à changer a priori.",
            })

    # 2. Option tarifaire (base vs HP/HC)
    pilotable_ecs = house.ecs in _ECS_PILOTABLE
    option = (house.option_tarifaire or "").lower()
    if option == "base" and pilotable_ecs:
        recos.append({
            "sujet": "Option tarifaire",
            "constat": "Vous êtes en option Base alors que votre ballon d'eau chaude est pilotable.",
            "conseil": "L'option Heures Pleines / Heures Creuses peut être intéressante si vous décalez le ballon "
                       "(et lave-linge, etc.) en heures creuses. À comparer selon votre profil.",
        })
    elif option in ("hphc", "hp/hc", "heures_creuses") and not pilotable_ecs:
        recos.append({
            "sujet": "Option tarifaire",
            "constat": "Vous êtes en Heures Pleines / Heures Creuses mais sans usage clairement déplaçable.",
            "conseil": "Sans usage à décaler en heures creuses, l'option Base est souvent plus avantageuse. À vérifier.",
        })

    # 3. Compatibilité tarif dynamique (type SOBRY)
    pilotables = _pilotables(house)
    risque = house.chauffage_principal in _CHAUFFAGE_ELEC_NON_PILOTABLE and house.regulation in (None, "aucune")
    if risque:
        compat = "prudence"
        compat_txt = ("Votre chauffage électrique n'est pas pilotable : un tarif dynamique fait courir un risque "
                      "de surcoût lors des pointes hivernales. À éviter sans régulation ni délestage.")
    elif pilotables:
        compat = "favorable"
        compat_txt = ("Votre profil (" + ", ".join(pilotables) + ") se prête bien à un tarif dynamique : "
                      "vous pouvez déplacer vos usages vers les heures peu chères.")
    else:
        compat = "neutre"
        compat_txt = ("Sans usage particulièrement pilotable, l'intérêt d'un tarif dynamique est incertain "
                      "pour votre profil. À étudier au cas par cas.")

    return {
        "recommandations": recos,
        "tarif_dynamique": {"compatibilite": compat, "explication": compat_txt, "usages_pilotables": pilotables},
        "avertissement": "Conseils indicatifs et indépendants, à confirmer avec vos factures. "
                         "HELIOS ne touche aucune commission sur ce conseil de niveau 1.",
    }
