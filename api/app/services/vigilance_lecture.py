"""Vigilance météo : la collecte (une pour toute la France) et sa lecture en base (phase 2).

`collecter_si_besoin` est le SEUL chemin vers Météo-France : lancé par un script (le planificateur
de production viendra à la mise en ligne), au plus toutes les heures, jamais par un foyer. Les
écrans et le chat lisent la table.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.vigilance import VigilanceDepartement
from app.services import meteofrance_vigilance as mf

logger = logging.getLogger("helios.vigilance")
GARDER_JOURS = 8  # les épisodes finis restent assez pour « Noter un dégât » (7 jours)


async def enregistrer(db: AsyncSession, episodes: list[dict], maintenant: datetime) -> int:
    """Remplace ce qui court encore par la carte du moment ; garde les épisodes finis récents."""
    limite = maintenant - timedelta(days=GARDER_JOURS)
    await db.execute(delete(VigilanceDepartement).where(
        or_(VigilanceDepartement.fin >= maintenant, VigilanceDepartement.fin < limite)))
    gardes = [e for e in episodes if e["fin"] >= limite]
    db.add_all([VigilanceDepartement(**e, collecte_le=maintenant) for e in gardes])
    await db.commit()
    return len(gardes)


async def derniere_collecte(db: AsyncSession) -> datetime | None:
    return await db.scalar(select(func.max(VigilanceDepartement.collecte_le)))


async def collecter_si_besoin(db: AsyncSession, maintenant: datetime | None = None, force: bool = False,
                              collecter=None) -> str:
    """Rend ce qui s'est passé : `dormant`, `recente`, `ok:<n>` ou `panne`. Ne lève jamais."""
    maintenant = maintenant or datetime.now(timezone.utc)
    if collecter is None and not mf.est_configure():
        return "dormant"
    derniere = await derniere_collecte(db)
    if not force and derniere and maintenant - derniere < timedelta(minutes=settings.vigilance_collecte_min_minutes):
        return "recente"
    try:
        episodes = await (collecter or mf.collecter)()
    except Exception as e:  # noqa: BLE001 — une panne laisse la table telle quelle
        logger.warning("Vigilance Météo-France indisponible : %s", e)
        return "panne"
    return f"ok:{await enregistrer(db, episodes, maintenant)}"


async def du_departement(db: AsyncSession, departement: str | None) -> list[VigilanceDepartement]:
    if not departement:
        return []
    return list(await db.scalars(select(VigilanceDepartement).where(VigilanceDepartement.departement == departement)))
