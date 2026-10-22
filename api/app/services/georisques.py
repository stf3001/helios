"""Client Géorisques : les risques recensés pour une COMMUNE (phase 2).

API publique du ministère de la Transition écologique, sans clé, 1 000 requêtes par minute et
par adresse IP. Routes lues dans sa documentation OpenAPI (georisques-api-v1) :

- `resultats_rapport_risque?code_insee=` : présence de chaque risque à l'échelle de la commune
  (naturels et technologiques) et lien du rapport — c'est la source de la liste ;
- `gaspar/catnat?code_insee=` : arrêtés de catastrophe naturelle (paginés) ;
- `radon?code_insee=` : classe de potentiel radon (1 à 3) ;
- `zonage_sismique?code_insee=` : zone de sismicité (1 à 5) ;
- `gaspar/pprn?codeInsee=` (attention : camelCase) : plans de prévention des risques naturels.

L'échelle reste la COMMUNE : Hélios ne demande jamais l'adresse. Les fonctions `normaliser*` sont
pures (testées sur des réponses enregistrées) ; `collecter` seul parle au réseau, avec un délai
court, et lève `GeorisquesIndisponible` au moindre écart — l'appelant journalise et se tait.
"""
from datetime import date

import httpx

BASE = "https://georisques.gouv.fr/api/v1"
DELAI_S = 8
CATNAT_ANNEES = 30

# La liste fermée, dans l'ordre d'affichage.
RISQUES = ("inondation", "argiles", "feux_de_foret", "mouvement_de_terrain", "seisme", "radon", "industriel",
           "autre")

# Clés du rapport de commune → liste fermée. Une clé inconnue (l'API évolue) tombe dans `autre`.
_NATURELS = {
    "inondation": "inondation", "remonteeNappe": "inondation", "risqueCotier": "inondation",
    "retraitGonflementArgile": "argiles",
    "feuForet": "feux_de_foret",
    "mouvementTerrain": "mouvement_de_terrain", "reculTraitCote": "mouvement_de_terrain",
    "seisme": "seisme",
    "radon": "radon",
    "avalanche": "autre", "eruptionVolcanique": "autre", "cyclone": "autre",
}
# Tous les risques technologiques (ICPE, nucléaire, canalisations, sols pollués, barrage, mines).
_TECHNOLOGIQUES = "industriel"


class GeorisquesIndisponible(Exception):
    pass


def _date_fr(texte: str | None) -> date | None:
    try:
        j, m, a = (int(x) for x in (texte or "").split("/"))
        return date(a, m, j)
    except ValueError:
        return None


def normaliser_rapport(rapport: dict) -> dict:
    """Le rapport de commune → {commune, risques (liste fermée, ordonnée, sans doublon), url}."""
    try:
        naturels = rapport["risquesNaturels"]
        technos = rapport["risquesTechnologiques"]
    except (KeyError, TypeError):
        raise GeorisquesIndisponible("Rapport de commune illisible : l'API a peut-être changé.")
    presents = set()
    for cle, v in (naturels or {}).items():
        if isinstance(v, dict) and v.get("present"):
            presents.add(_NATURELS.get(cle, "autre"))
    if any(isinstance(v, dict) and v.get("present") for v in (technos or {}).values()):
        presents.add(_TECHNOLOGIQUES)
    commune = (rapport.get("commune") or {}).get("libelle")
    return {"commune": commune, "risques": [r for r in RISQUES if r in presents], "url": rapport.get("url")}


def compter_catnat(arretes: list[dict], aujourd_hui: date) -> int:
    """Arrêtés dont l'événement a commencé dans les 30 dernières années."""
    limite = date(aujourd_hui.year - CATNAT_ANNEES, aujourd_hui.month, min(aujourd_hui.day, 28))
    return sum(1 for a in arretes if (d := _date_fr(a.get("date_debut_evt"))) is not None and d >= limite)


def normaliser_radon(reponse: dict) -> int | None:
    data = (reponse or {}).get("data") or []
    try:
        return int(data[0]["classe_potentiel"]) if data else None
    except (KeyError, ValueError, TypeError):
        return None


def normaliser_sismique(reponse: dict) -> int | None:
    data = (reponse or {}).get("data") or []
    try:
        return int(data[0]["code_zone"]) if data else None
    except (KeyError, ValueError, TypeError):
        return None


def normaliser_pprn(reponse: dict) -> bool | None:
    """Un plan de prévention des risques naturels existe-t-il ? None si la réponse est illisible."""
    total = (reponse or {}).get("totalElements")
    return total > 0 if isinstance(total, int) else None


async def _get(client: httpx.AsyncClient, route: str, params: dict) -> dict:
    r = await client.get(f"{BASE}/{route}", params=params)
    if r.status_code != 200 or not r.text.strip():
        raise GeorisquesIndisponible(f"{route} : HTTP {r.status_code}")
    try:
        return r.json()
    except ValueError:
        raise GeorisquesIndisponible(f"{route} : réponse non JSON")


async def collecter(code_insee: str, aujourd_hui: date | None = None,
                    client: httpx.AsyncClient | None = None) -> dict:
    """Interroge Géorisques pour une commune ; renvoie les seuls champs gardés."""
    jour = aujourd_hui or date.today()
    propre = client is None
    client = client or httpx.AsyncClient(timeout=DELAI_S)
    try:
        rapport = normaliser_rapport(await _get(client, "resultats_rapport_risque", {"code_insee": code_insee}))
        arretes, page = [], 1
        while True:
            r = await _get(client, "gaspar/catnat", {"code_insee": code_insee, "page": page, "page_size": 100})
            arretes += r.get("data") or []
            if page >= (r.get("total_pages") or 1) or page >= 20:
                break
            page += 1
        radon = normaliser_radon(await _get(client, "radon", {"code_insee": code_insee}))
        sismique = normaliser_sismique(await _get(client, "zonage_sismique", {"code_insee": code_insee}))
        ppr = normaliser_pprn(await _get(client, "gaspar/pprn", {"codeInsee": code_insee, "page_size": 1}))
    except httpx.HTTPError as e:
        raise GeorisquesIndisponible(f"réseau : {e.__class__.__name__}")
    finally:
        if propre:
            await client.aclose()
    return {**rapport, "catnat_30_ans": compter_catnat(arretes, jour), "radon_classe": radon,
            "zone_sismique": sismique, "ppr": ppr}
