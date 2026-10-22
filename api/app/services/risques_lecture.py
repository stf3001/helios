"""Risques d'une commune, gardés en base 30 jours au plus (phase 2).

Une panne de Géorisques (réseau, API changée) ne bloque JAMAIS l'espace : l'erreur est
journalisée, et l'on rend ce qu'on a — une collecte plus ancienne (affichée avec sa date), ou
rien, et la section ne s'affiche pas.
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risques import RisquesCommune
from app.services import georisques

logger = logging.getLogger("helios.georisques")
FRAICHEUR = timedelta(days=30)
GEO_API = "https://geo.api.gouv.fr/communes"


async def risques_de_la_commune(db: AsyncSession, code_insee: str | None, maintenant: datetime | None = None,
                                collecter=None) -> RisquesCommune | None:
    if not code_insee:
        return None
    maintenant = maintenant or datetime.now(timezone.utc)
    ligne = await db.get(RisquesCommune, code_insee)
    if ligne is not None and maintenant - ligne.collecte_le < FRAICHEUR:
        return ligne
    try:
        r = await (collecter or georisques.collecter)(code_insee)
    except Exception as e:  # noqa: BLE001 — quelle qu'elle soit, une panne ne casse pas l'espace
        logger.warning("Géorisques indisponible pour %s : %s", code_insee, e)
        return ligne
    if ligne is None:
        ligne = RisquesCommune(code_insee=code_insee)
        db.add(ligne)
    ligne.commune, ligne.risques, ligne.url_rapport = r["commune"], r["risques"], r["url"]
    ligne.catnat_30_ans, ligne.radon_classe = r["catnat_30_ans"], r["radon_classe"]
    ligne.zone_sismique, ligne.ppr, ligne.collecte_le = r["zone_sismique"], r["ppr"], maintenant
    await db.commit()
    return ligne


async def communes_du_code_postal(code_postal: str) -> list[dict]:
    """[{code_insee, nom}] — API Découpage administratif (geo.api.gouv.fr), publique. Lève si indisponible."""
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(GEO_API, params={"codePostal": code_postal, "fields": "nom,code"})
        r.raise_for_status()
        return sorted(({"code_insee": c["code"], "nom": c["nom"]} for c in r.json()), key=lambda c: c["nom"])
