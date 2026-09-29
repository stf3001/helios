"""Le jardin nourricier — combien de legumes, sur quelle surface, pour quel temps.

CE CALCUL EST RETOURNE, ET C'EST LE POINT IMPORTANT.

La demande d'origine etait : « le visiteur donne un nombre de personnes, on repond des
kilos, des m2 et un temps d'entretien — et ce temps ne doit jamais depasser une heure,
pour ne pas decourager les debutants ». Pris dans ce sens, le calcul ment : nourrir
quatre personnes en legumes demande deux bonnes heures par jour en moyenne, et afficher
« 1 h » serait un chiffre faux sur un site dont l'argument est le parler-vrai.

On pose donc le TEMPS EN ENTREE, comme une contrainte, et on repond ce qu'il achete :
« une heure par jour, c'est 150 m2, et un tiers de vos legumes ». Le debutant ne voit
plus une montagne, il voit un gain reel, et personne n'a eu besoin de tronquer un
chiffre. Ce que couterait l'autonomie complete est calcule aussi, et montre — plus bas,
sans en faire le titre.

Deux autres honnetetes, tenues par le code et pas par une note de bas de page :

1. UN POTAGER NE NOURRIT PAS, IL DONNE DES LEGUMES. 127 kg de legumes par personne et
   par an, ce n'est qu'une part de l'alimentation. Le vocabulaire de sortie dit
   « legumes », jamais « nourrir » — c'est un mot, et il nous evite une promesse
   intenable.
2. LA MOYENNE ANNUELLE CACHE TOUT. Le travail se concentre de mars a juin. Une moyenne
   lissee ferait abandonner en juin, qui est justement le moment ou les debutants
   lachent. Le calcul sort donc aussi le mois de pointe, et la repartition mensuelle.

Aucune I/O, aucune dependance a la base : tout est pur et testable. Les hypotheses
vivent dans `config.py` sous `jardin_*`, chacune avec sa source, et remontent a l'ecran.
"""

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.services.regions import departement_du_code_postal

MOIS = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)

#: Libellés affichés, avec leurs accents — MOIS sert aux clés et aux comparaisons.
MOIS_AFFICHES = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)

_DOSSIER = Path(__file__).resolve().parents[2] / "data" / "jardin"

CONDUITES = ("debutant", "rodee")

#: Les deux zones de jardinage. Le decoupage tient en une phrase — « au sud de la Loire,
#: plus la vallee du Rhone mediterraneenne » — et c'est volontaire : ce calculateur n'a
#: pas vocation a etre precis, il a vocation a etre juste sur l'ordre de grandeur.
#:
#: CE QU'IL FAUT SAVOIR SUR CE DECOUPAGE : pour un potager, ce qui commande le calendrier
#: c'est la date des dernieres gelees, et la-dessus Strasbourg ressemble davantage a Lille
#: qu'a Nantes. Un decoupage nord / sud / est continental serait plus juste. Deux zones
#: est un choix assume, affinable plus tard sans toucher au reste : seule cette table
#: changerait.
_REGIONS_SUD = ("occ", "pac", "cor", "naq")
_DEPARTEMENTS_SUD_HORS_REGION = ("07", "26")  # Ardeche et Drome : climat du Midi


def zone(code_postal: str | None) -> str | None:
    """« nord » ou « sud » a partir d'un code postal, ou None s'il est illisible."""
    departement = departement_du_code_postal(code_postal or "")
    if departement is None:
        return None
    return zone_du_departement(departement)


def zone_du_departement(departement: str) -> str | None:
    from app.services.regions import region_du_departement

    cible = (departement or "").upper()
    if cible in _DEPARTEMENTS_SUD_HORS_REGION:
        return "sud"
    region = region_du_departement(cible)
    if region is None:
        return None
    return "sud" if region in _REGIONS_SUD else "nord"


def _table(paires: tuple[tuple[str, float], ...], cle: str) -> float:
    for nom, valeur in paires:
        if nom == cle:
            return valeur
    raise ValueError(f"conduite inconnue : {cle}")


def besoin_kg_an(personnes: int) -> float:
    """Les legumes que ce foyer mange en un an, pommes de terre comprises."""
    return personnes * settings.jardin_legumes_kg_personne_an


def _totale_depuis_cultivee(cultivee_m2: float) -> float:
    """La surface du terrain : les allees, le compost et la cabane ne produisent rien."""
    return cultivee_m2 / (1 - settings.jardin_part_allees_pct / 100)


def calcul(
    personnes: int,
    heures_jour: float | None = None,
    conduite: str = "debutant",
    code_postal: str | None = None,
) -> dict:
    """Ce qu'un budget de temps donne, et ce que couterait l'autonomie complete.

    `heures_jour` est une CONTRAINTE D'ENTREE, pas un resultat : c'est le temps que le
    visiteur accepte d'y passer, en moyenne sur l'annee.
    """
    if conduite not in CONDUITES:
        raise ValueError(f"conduite inconnue : {conduite}")
    if not 1 <= personnes <= settings.jardin_personnes_max:
        raise ValueError(f"nombre de personnes hors bornes : {personnes}")

    budget_jour = settings.jardin_heures_jour_defaut if heures_jour is None else heures_jour
    if not settings.jardin_heures_jour_min <= budget_jour <= settings.jardin_heures_jour_max:
        raise ValueError(f"budget de temps hors bornes : {budget_jour}")

    rendement = _table(settings.jardin_rendement_kg_m2_an, conduite)
    temps_m2 = _table(settings.jardin_temps_h_m2_an, conduite)

    besoin = besoin_kg_an(personnes)

    # --- Ce que l'autonomie complete demanderait, calculee d'abord : elle sert de plafond ---
    cultivee_totale = besoin / rendement
    heures_an_totale = cultivee_totale * temps_m2

    # --- Ce que le budget de temps achete, plafonne au besoin reel ---
    # Sans ce plafond, une personne seule avec trois heures par jour se verrait proposer
    # 400 m2 et 800 kg de legumes : un jardin qui produit pour la moitie du quartier.
    heures_an_budget = min(budget_jour * 365, heures_an_totale)
    cultivee = heures_an_budget / temps_m2
    recolte = cultivee * rendement
    couverture = recolte / besoin * 100 if besoin else 0.0

    saison = settings.jardin_saison_pct
    mensuel = [
        {
            "mois": i + 1,
            "nom": MOIS[i],
            "heures": round(heures_an_budget * part / 100, 1),
            # Le mois n'a pas 30,4 jours partout, mais la precision d'un calendrier exact
            # serait fausse ici : l'incertitude porte sur la repartition elle-meme.
            "heures_jour": round(heures_an_budget * part / 100 / 30.4, 2),
        }
        for i, part in enumerate(saison)
    ]
    pointe = max(mensuel, key=lambda m: m["heures"])

    return {
        "personnes": personnes,
        "conduite": conduite,
        "zone": zone(code_postal),
        "besoin_kg_an": round(besoin),
        # Ce que le budget de temps permet
        "budget_heures_jour": round(heures_an_budget / 365, 2),
        "surface_cultivee_m2": round(cultivee),
        "surface_totale_m2": round(_totale_depuis_cultivee(cultivee)),
        "recolte_kg_an": round(recolte),
        "couverture_pct": round(min(couverture, 100)),
        "heures_an": round(heures_an_budget),
        "mensuel": mensuel,
        "pointe": {"mois": pointe["nom"], "heures_jour": pointe["heures_jour"]},
        # Ce que couterait la totalite — montre, mais pas en titre
        "autonomie": {
            "surface_cultivee_m2": round(cultivee_totale),
            "surface_totale_m2": round(_totale_depuis_cultivee(cultivee_totale)),
            "heures_jour": round(heures_an_totale / 365, 2),
            "atteinte": couverture >= 99.5,
        },
        "hypotheses": hypotheses(conduite),
        # Les textes AFFICHÉS portent leurs accents — seuls les commentaires et les
        # identifiants s'en passent. Une phrase sans accents est une phrase fautive
        # dès qu'elle arrive à l'écran.
        "avertissement": (
            "Ordres de grandeur, pas une promesse : un potager dépend du sol, de "
            "l'exposition, de la météo de l'année et de l'expérience du jardinier. "
            "Un terrain qui reçoit moins de six heures de soleil par jour produit "
            "nettement moins. Ces chiffres servent à se faire une idée avant de "
            "bêcher, pas à planifier une récolte."
        ),
    }


@lru_cache(maxsize=1)
def _calendrier() -> dict:
    return json.loads((_DOSSIER / "calendrier.json").read_text(encoding="utf-8"))


def programme(code_postal: str | None) -> dict:
    """Le programme annuel de cultures, pour la zone du visiteur.

    DONNEE VERSIONNEE, PAS UN CALCUL : le calendrier vit dans
    `api/data/jardin/calendrier.json`, a cote du code, et se corrige en editant ce
    fichier. Aucun appel sortant, aucun modele — un calendrier de semis est un fait
    etabli, pas quelque chose qu'on demande a une IA d'inventer.

    Faute de code postal lisible, on sert la zone NORD : c'est la plus tardive des deux,
    donc celle qui fait le moins de degats quand on se trompe. Conseiller un semis trop
    tot fait perdre des plants ; le conseiller trop tard fait perdre quinze jours.
    """
    z = zone(code_postal) or "nord"
    source = _calendrier()
    legumes = [
        {
            "nom": legume["nom"],
            "famille": legume["famille"],
            "facile": legume["facile"],
            "note": legume["note"],
            **legume[z],
        }
        for legume in source["legumes"]
    ]
    return {
        "zone": z,
        "zone_deduite": zone(code_postal) is not None,
        "version": source["version"],
        "avertissement": source["avertissement"],
        "mois": [
            {"numero": i + 1, "nom": MOIS_AFFICHES[i]} for i in range(12)
        ],
        "legumes": legumes,
    }


def hypotheses(conduite: str) -> list[dict]:
    """Ce sur quoi le calcul repose, tel qu'il s'affiche sous le resultat.

    Rien n'est cache : chaque chiffre porte sa valeur, son unite et son statut. C'est la
    meme regle que le simulateur solaire, et c'est ce qui rend le calcul discutable.
    """
    return [
        {
            "cle": "Légumes mangés par personne",
            "valeur": f"{settings.jardin_legumes_kg_personne_an:.0f} kg/an",
            "statut": "relevé",
            "detail": "Pommes de terre comprises. 508 kg pour une famille de quatre.",
        },
        {
            "cle": "Rendement de la surface cultivée",
            "valeur": f"{_table(settings.jardin_rendement_kg_m2_an, conduite):.1f} kg/m²/an",
            "statut": "relevé",
            "detail": (
                "Les potagers domestiques mesurés vont de 0,5 à 3,9 kg/m², moyenne "
                "proche de 1,8. On retient le bas pour un débutant, le haut pour un "
                "jardin rodé — jamais le record."
            ),
        },
        {
            "cle": "Temps d'entretien",
            "valeur": f"{_table(settings.jardin_temps_h_m2_an, conduite):.1f} h/m²/an",
            "statut": "relevé",
            "detail": (
                "Les témoignages tournent autour de 260 à 365 heures par an pour "
                "100 m². Le paillage et l'arrosage automatique font la différence."
            ),
        },
        {
            "cle": "Part non cultivée",
            "valeur": f"{settings.jardin_part_allees_pct:.0f} %",
            "statut": "à confirmer",
            "detail": "Allées, compost, cabane, bordures : ils prennent de la place sans produire.",
        },
        {
            "cle": "Répartition dans l'année",
            "valeur": "mars à juin = la moitié du travail",
            "statut": "à confirmer",
            "detail": (
                "La forme compte plus que la valeur exacte : une moyenne annuelle "
                "lissée ferait croire à un effort régulier, ce qu'un potager n'est pas."
            ),
        },
    ]
