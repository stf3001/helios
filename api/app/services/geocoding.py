"""Géocodage adresse → GPS via l'API Adresse (data.gouv.fr, gratuite, sans clé) — doc 09 §1."""

import httpx

_BASE = "https://api-adresse.data.gouv.fr/search/"


class GeocodingError(Exception):
    pass


async def geocode(address: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(_BASE, params={"q": address, "limit": 1})
        res.raise_for_status()
        features = res.json().get("features", [])

    if not features:
        raise GeocodingError(f"Adresse introuvable : {address}")

    feature = features[0]
    lon, lat = feature["geometry"]["coordinates"]
    props = feature["properties"]
    return {
        "lat": lat,
        "lon": lon,
        "label": props.get("label"),
        "code_postal": props.get("postcode"),
        "citycode": props.get("citycode"),
    }
