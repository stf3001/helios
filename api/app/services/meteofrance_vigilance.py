"""Vigilance météo de Météo-France — API « Bulletin Vigilance » (`DonneesPubliquesVigilance`), phase 2.

DORMANT SANS CLÉ, comme le client Enedis : tant que `METEOFRANCE_API_KEY` est vide, aucun appel
n'est tenté et rien ne s'affiche. L'API est gratuite mais demande un compte sur
portail-api.meteofrance.fr (démarche de Stéphane).

Format lu dans la documentation officielle (Confluence « OPEN DATA METEO-FRANCE », page « API
Bulletin Vigilance ») : produit « carte » `GET /public/DPVigilance/v1/cartevigilance/encours` →
`product.periods[]` (J, J+1) → `timelaps.domain_ids[]` (département ; `XX10` = son littoral) →
`phenomenon_items[]` (`phenomenon_id` 1 à 9) → `timelaps_items[]` (`begin_time`, `end_time`,
`color_id` 1 vert, 2 jaune, 3 orange, 4 rouge).

On ne garde que l'ORANGE et le ROUGE, regroupés en épisodes (créneaux contigus d'un même
phénomène), réduits à : département, phénomène (liste fermée), couleur, début, fin. Le texte du
bulletin n'est jamais repris : Hélios affiche ses gestes et renvoie vers la carte officielle.
"""
from datetime import datetime

import httpx

from app.core.config import settings

URL_CARTE = "https://public-api.meteofrance.fr/public/DPVigilance/v1/cartevigilance/encours"
CARTE_OFFICIELLE = "https://vigilance.meteofrance.fr/fr"
DELAI_S = 15

PHENOMENES = ("vent", "orages", "pluie_inondation", "canicule", "grand_froid", "neige_verglas", "autre")
# Numérotation Météo-France. Les crues se préparent comme la pluie-inondation ; avalanches et
# vagues-submersion n'ont pas de gestes dans la fiche : « autre » (pastille et lien seulement).
_PHENOMENES = {"1": "vent", "2": "pluie_inondation", "3": "orages", "4": "pluie_inondation", "5": "neige_verglas",
               "6": "canicule", "7": "grand_froid", "8": "autre", "9": "autre"}
_COULEURS = {3: "orange", 4: "rouge"}


class VigilanceIndisponible(Exception):
    pass


def est_configure() -> bool:
    return bool(settings.meteofrance_api_key)


def _entetes() -> dict:
    # L'API (WSO2) accepte la clé d'API dans l'en-tête `apikey`, ou un jeton OAuth2 en Bearer.
    return {"accept": "application/json", "apikey": settings.meteofrance_api_key}


def _instant(texte: str) -> datetime:
    return datetime.fromisoformat(texte.replace("Z", "+00:00"))


def _departement(domain_id: str) -> str | None:
    """`83` → 83, `2A` → 2A, `8310` (littoral du Var) → 83 ; le reste (FRA, zones) est ignoré."""
    if len(domain_id) == 2 and domain_id.isalnum():
        return domain_id
    if len(domain_id) == 4 and domain_id.endswith("10"):
        return domain_id[:2]
    return None


def normaliser_carte(carte: dict) -> list[dict]:
    """Le produit « carte » → épisodes orange/rouge : {departement, phenomene, couleur, debut, fin}."""
    try:
        periodes = carte["product"]["periods"]
    except (KeyError, TypeError):
        raise VigilanceIndisponible("Produit « carte » illisible : l'API a peut-être changé.")
    creneaux: dict[tuple, list] = {}
    for periode in periodes:
        for dom in (periode.get("timelaps") or {}).get("domain_ids") or []:
            dep = _departement(str(dom.get("domain_id", "")))
            if dep is None:
                continue
            for ph in dom.get("phenomenon_items") or []:
                phen = _PHENOMENES.get(str(ph.get("phenomenon_id")), "autre")
                for t in ph.get("timelaps_items") or []:
                    if t.get("color_id") in _COULEURS:
                        creneaux.setdefault((dep, phen), []).append(
                            (_instant(t["begin_time"]), _instant(t["end_time"]), t["color_id"]))
    episodes = []
    for (dep, phen), liste in creneaux.items():
        liste.sort()
        courant = None
        for debut, fin, couleur in liste:
            if courant and debut <= courant["fin"]:            # contigu ou chevauchant : même épisode
                courant["fin"] = max(courant["fin"], fin)
                courant["c"] = max(courant["c"], couleur)
            else:
                courant = {"departement": dep, "phenomene": phen, "debut": debut, "fin": fin, "c": couleur}
                episodes.append(courant)
    return [{**{k: v for k, v in e.items() if k != "c"}, "couleur": _COULEURS[e["c"]]} for e in episodes]


async def collecter(client: httpx.AsyncClient | None = None) -> list[dict]:
    """UN appel pour toute la France. Lève sans clé : ne jamais appeler à vide."""
    if not est_configure():
        raise VigilanceIndisponible("METEOFRANCE_API_KEY vide : module dormant.")
    propre = client is None
    client = client or httpx.AsyncClient(timeout=DELAI_S)
    try:
        r = await client.get(URL_CARTE, headers=_entetes())
        if r.status_code != 200:
            raise VigilanceIndisponible(f"carte : HTTP {r.status_code}")
        return normaliser_carte(r.json())
    except (httpx.HTTPError, ValueError) as e:
        raise VigilanceIndisponible(f"carte : {e.__class__.__name__}")
    finally:
        if propre:
            await client.aclose()
