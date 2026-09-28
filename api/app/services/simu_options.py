"""Options chiffrées, prochaine étape et objectifs — étape 1.

Trois options, chacune dimensionnée à sa taille la plus rentable :
  1. batterie virtuelle   2. batterie physique   3. pilotage sans stockage

La recommandation est le meilleur gain net sur 25 ans, point. Si le foyer a coché
« besoin de secours en cas de coupure », la batterie physique est présentée comme un
choix de confort, avec son coût réel — on ne maquille pas sa rentabilité pour la faire
gagner, et on ne la cache pas non plus.

RÈGLE STRUCTURANTE : la « prochaine étape » sort du MÊME moteur et des MÊMES tailles que
les options. C'est la seule façon d'éviter qu'une suggestion contredise la recommandation
affichée deux écrans plus loin — un test le vérifie.
"""

from app.core.config import settings
from app.services import simu_engine, simu_pv
from app.services.simu_conso import ProfilConso
from app.services.simu_types import Configuration, Stockage


def _evaluer(config: Configuration, profil: ProfilConso, production_ref: dict) -> dict:
    """Passe le moteur sur une variante, sans jamais rappeler PVGIS.

    `detail=False` : la recherche fait des dizaines de passages et n'a besoin ni des
    bilans mensuels ni des journées moyennes.
    """
    prod_h = simu_pv.recomposer(production_ref, config.panneaux.nb_panneaux)
    return simu_engine.calculer(config, profil, prod_h, detail=False)


def _plafond_panneaux(config: Configuration) -> int:
    plafond = settings.simu_panneaux_max
    du_toit = simu_pv.panneaux_max_du_toit(config.panneaux.surface_toit_m2)
    return min(plafond, du_toit) if du_toit else plafond


def _meilleure_taille(
    config: Configuration, profil: ProfilConso, production_ref: dict, stockage: Stockage
) -> dict:
    """Cherche panneau par panneau la taille la plus rentable pour un type de stockage.

    Un panneau de plus n'est retenu que si son gain annuel supplémentaire rapporte plus que
    `simu_seuil_rendement_marginal_pct` de ce qu'il coûte. Au tarif de rachat actuel, ce
    critère s'arrête vite de lui-même : au-delà de l'autoconsommation, un panneau ne
    rapporte presque rien.
    """
    seuil = settings.simu_seuil_rendement_marginal_pct / 100
    plafond = _plafond_panneaux(config)
    carport = config.panneaux.nb_panneaux_carport

    meilleur = None
    precedent = None
    for nb in range(1, plafond + 1):
        variante = config.avec(panneaux=config.panneaux.__class__(
            nb_panneaux=nb,
            orientation=config.panneaux.orientation,
            inclinaison=config.panneaux.inclinaison,
            ombrage=config.panneaux.ombrage,
            nb_panneaux_carport=carport,
            surface_toit_m2=config.panneaux.surface_toit_m2,
        ), stockage=stockage)
        resultat = _evaluer(variante, profil, production_ref)

        if precedent is not None:
            delta_cout = (resultat["investissement"]["total_eur"]
                          - precedent["investissement"]["total_eur"])
            delta_gain = (resultat["indicateurs"]["economie_1re_annee_eur"]
                          - precedent["indicateurs"]["economie_1re_annee_eur"])
            if delta_cout > 0 and delta_gain / delta_cout < seuil:
                break

        meilleur = {"nb_panneaux": nb, "config": variante, "resultat": resultat}
        precedent = resultat

    if meilleur is None:  # plafond à 0 panneau : rien à proposer
        variante = config.avec(stockage=stockage)
        meilleur = {"nb_panneaux": 0, "config": variante,
                    "resultat": _evaluer(variante, profil, production_ref)}
    return meilleur


def _resume(nom: str, label: str, candidat: dict, secours: bool) -> dict:
    r = candidat["resultat"]
    ind = r["indicateurs"]
    return {
        "code": nom,
        "label": label,
        "nb_panneaux": candidat["nb_panneaux"],
        "puissance_kwc": ind["puissance_kwc"],
        "investissement_eur": r["investissement"]["total_eur"],
        "tva_pct": r["investissement"]["tva_pct"],
        "autonomie_pct": ind["autonomie_pct"],
        "facture_mois_eur": ind["facture_mois_eur"],
        "economie_1re_annee_eur": ind["economie_1re_annee_eur"],
        "gain_net_25_ans_eur": ind["gain_net_25_ans_eur"],
        "temps_retour_ans": ind["temps_retour_ans"],
        "rendement_annuel_pct": ind["rendement_annuel_pct"],
        "configuration": {
            "nb_panneaux": candidat["config"].panneaux.nb_panneaux,
            "nb_panneaux_carport": candidat["config"].panneaux.nb_panneaux_carport,
            "nb_packs": candidat["config"].stockage.nb_packs,
            "batterie_virtuelle": candidat["config"].stockage.batterie_virtuelle,
            "pilotage": candidat["config"].stockage.pilotage,
        },
        "secours_possible": nom == "batterie_physique",
        "note_secours": (
            "Vous avez indiqué vouloir tenir en cas de coupure : seule la batterie physique "
            "le permet. C'est un choix de confort — son coût et sa rentabilité sont affichés "
            "tels quels, sans arrangement."
        ) if (secours and nom == "batterie_physique") else None,
    }


def _offre_virtuelle_par_defaut() -> str | None:
    from app.services import batterie_virtuelle
    disponibles = batterie_virtuelle.offres()
    # À grille égale, on part de l'offre complète : une grille incomplète produirait un
    # chiffrage provisoire présenté comme une recommandation.
    for code, offre in disponibles.items():
        if offre.grille_complete:
            return code
    return next(iter(disponibles), None)


def calculer_options(config: Configuration, profil: ProfilConso, production_ref: dict) -> dict:
    """Les trois options, la recommandation, la prochaine étape et les objectifs."""
    secours = config.maison.besoin_secours
    base = config.stockage

    candidats = {
        "batterie_virtuelle": _meilleure_taille(config, profil, production_ref, Stockage(
            nb_packs=0, batterie_virtuelle=_offre_virtuelle_par_defaut(), pilotage=False)),
        "batterie_physique": _meilleure_taille(config, profil, production_ref, Stockage(
            nb_packs=max(base.nb_packs, 1), batterie_virtuelle=None, pilotage=True)),
        "pilotage": _meilleure_taille(config, profil, production_ref, Stockage(
            nb_packs=0, batterie_virtuelle=None, pilotage=True)),
    }

    libelles = {
        "batterie_virtuelle": "Batterie virtuelle",
        "batterie_physique": "Batterie physique",
        "pilotage": "Pilotage, sans stockage",
    }
    options = [_resume(code, libelles[code], candidat, secours) for code, candidat in candidats.items()]
    options.sort(key=lambda o: o["gain_net_25_ans_eur"], reverse=True)
    recommandee = options[0]["code"] if options else None

    actuel = _evaluer(config, profil, production_ref)
    etape = _prochaine_etape(config, profil, production_ref, actuel, candidats, recommandee)

    return {
        "options": options,
        "recommandee": recommandee,
        "prochaine_etape": etape,
        "objectifs": objectifs(actuel),
    }


def _prochaine_etape(
    config: Configuration,
    profil: ProfilConso,
    production_ref: dict,
    actuel: dict,
    candidats: dict,
    recommandee: str | None,
) -> dict | None:
    """L'action au meilleur rapport gain / euro investi, depuis la configuration courante.

    Les tailles proposées sont celles des options : la suggestion ne peut donc pas
    recommander une installation que l'écran Étude déconseille.
    """
    gain_actuel = actuel["indicateurs"]["economie_1re_annee_eur"]
    cout_actuel = actuel["investissement"]["total_eur"]
    pistes: list[dict] = []

    def ajouter(libelle: str, variante: Configuration, application: dict):
        resultat = _evaluer(variante, profil, production_ref)
        delta_gain = resultat["indicateurs"]["economie_1re_annee_eur"] - gain_actuel
        delta_cout = resultat["investissement"]["total_eur"] - cout_actuel
        if delta_gain <= 0:
            return
        rapport = delta_gain / delta_cout if delta_cout > 0 else float("inf")
        pistes.append({
            "libelle": libelle,
            "gain_annuel_eur": round(delta_gain),
            "investissement_eur": round(delta_cout),
            "rapport": rapport,
            "appliquer": application,
        })

    # 1. Aller à la taille de panneaux de l'option recommandée.
    if recommandee and candidats.get(recommandee):
        cible = candidats[recommandee]["nb_panneaux"]
        manque = cible - config.panneaux.nb_panneaux
        if manque > 0:
            ajouter(
                f"Poser {manque} panneau{'x' if manque > 1 else ''} sur le toit",
                config.avec(panneaux=config.panneaux.__class__(
                    nb_panneaux=cible, orientation=config.panneaux.orientation,
                    inclinaison=config.panneaux.inclinaison, ombrage=config.panneaux.ombrage,
                    nb_panneaux_carport=config.panneaux.nb_panneaux_carport,
                    surface_toit_m2=config.panneaux.surface_toit_m2)),
                {"nb_panneaux": cible},
            )

    # 2. Activer le pilotage — le geste qui ne coûte presque rien.
    if not config.stockage.pilotage and profil.nb_usages_pilotables() > 0:
        ajouter("Activer le pilotage des usages",
                config.avec(stockage=Stockage(
                    nb_packs=config.stockage.nb_packs,
                    batterie_virtuelle=config.stockage.batterie_virtuelle,
                    palier_virtuel_kwh=config.stockage.palier_virtuel_kwh, pilotage=True)),
                {"pilotage": True})

    # 3. Activer la batterie virtuelle.
    if not config.stockage.batterie_virtuelle:
        offre = _offre_virtuelle_par_defaut()
        if offre:
            ajouter("Activer la batterie virtuelle",
                    config.avec(stockage=Stockage(
                        nb_packs=config.stockage.nb_packs, batterie_virtuelle=offre,
                        pilotage=config.stockage.pilotage)),
                    {"batterie_virtuelle": offre})

    # 4. Ajouter un pack de batterie physique.
    if config.stockage.nb_packs < settings.simu_batterie_packs_max:
        ajouter("Ajouter un pack de batterie",
                config.avec(stockage=Stockage(
                    nb_packs=config.stockage.nb_packs + 1,
                    batterie_virtuelle=config.stockage.batterie_virtuelle,
                    palier_virtuel_kwh=config.stockage.palier_virtuel_kwh,
                    pilotage=config.stockage.pilotage)),
                {"nb_packs": config.stockage.nb_packs + 1})

    # 5. Réduire la puissance quand l'écrêtage fait perdre de l'énergie payée.
    if actuel["bilan_annuel"]["ecrete"] > 0 and config.panneaux.nb_panneaux > 1:
        cible = max(config.panneaux.nb_panneaux - 2, 1)
        variante = config.avec(panneaux=config.panneaux.__class__(
            nb_panneaux=cible, orientation=config.panneaux.orientation,
            inclinaison=config.panneaux.inclinaison, ombrage=config.panneaux.ombrage,
            nb_panneaux_carport=config.panneaux.nb_panneaux_carport,
            surface_toit_m2=config.panneaux.surface_toit_m2))
        resultat = _evaluer(variante, profil, production_ref)
        economie_invest = cout_actuel - resultat["investissement"]["total_eur"]
        perte_gain = gain_actuel - resultat["indicateurs"]["economie_1re_annee_eur"]
        if economie_invest > 0 and perte_gain <= 0:
            pistes.append({
                "libelle": f"Retirer {config.panneaux.nb_panneaux - cible} panneaux : "
                           "ils produisent sans pouvoir sortir",
                "gain_annuel_eur": round(-perte_gain),
                "investissement_eur": -round(economie_invest),
                "rapport": float("inf"),
                "appliquer": {"nb_panneaux": cible},
            })

    if not pistes:
        return None
    meilleure = max(pistes, key=lambda p: p["rapport"])
    meilleure.pop("rapport", None)
    return meilleure


def objectifs(resultat: dict) -> list[dict]:
    """Les objectifs cochés automatiquement d'après le résultat courant."""
    ind = resultat["indicateurs"]
    facture = ind["facture_mois_eur"]
    reference = ind["facture_mois_reference_eur"] or 1.0
    retour = ind["temps_retour_ans"]

    return [
        {"code": "autonomie",
         "libelle": f"Couvrir {settings.simu_objectif_autonomie_pct:g} % de ma consommation",
         "atteint": ind["autonomie_pct"] >= settings.simu_objectif_autonomie_pct,
         "valeur": f"{ind['autonomie_pct']:g} %"},
        {"code": "facture",
         "libelle": "Diviser ma facture par deux",
         "atteint": facture <= reference / 2,
         "valeur": f"{facture:g} € au lieu de {reference:g} €"},
        {"code": "retour",
         "libelle": f"Rentabiliser en moins de {settings.simu_objectif_retour_ans} ans",
         "atteint": retour is not None and retour <= settings.simu_objectif_retour_ans,
         "valeur": f"{retour} ans" if retour is not None else "non rentabilisé sur 25 ans"},
        {"code": "tva",
         "libelle": "Rester à TVA 5,5 %",
         "atteint": resultat["investissement"]["tva_pct"] == settings.simu_tva_reduite_pct,
         "valeur": f"{resultat['investissement']['tva_pct']:g} %"},
        {"code": "pilotage",
         "libelle": f"Piloter au moins {settings.simu_objectif_usages_pilotes} usages",
         "atteint": ind["nb_usages_pilotes"] >= settings.simu_objectif_usages_pilotes,
         "valeur": f"{ind['nb_usages_pilotes']} usage(s)"},
    ]
