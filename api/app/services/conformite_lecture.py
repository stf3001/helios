"""Lit en base ce dont `conformite` (pur) a besoin : justificatifs et charte en vigueur."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Charte, PartnerDocument
from app.services import conformite


async def charte_en_vigueur(db: AsyncSession) -> Charte | None:
    return await db.scalar(select(Charte).order_by(Charte.created_at.desc(), Charte.version.desc()).limit(1))


async def documents_par_partenaire(db: AsyncSession, ids) -> dict:
    ids = list(ids)
    out = {i: [] for i in ids}
    if ids:
        for d in await db.scalars(select(PartnerDocument).where(PartnerDocument.partner_id.in_(ids))):
            out[d.partner_id].append(d)
    return out


async def en_regle(db: AsyncSession, partenaires, aujourd_hui: date | None = None) -> set:
    """Les identifiants des partenaires en règle, en deux requêtes quel que soit leur nombre."""
    partenaires = list(partenaires)
    charte = await charte_en_vigueur(db)
    version = charte.version if charte else None
    docs = await documents_par_partenaire(db, (p.id for p in partenaires))
    jour = aujourd_hui or date.today()
    return {p.id for p in partenaires
            if conformite.en_regle(bool(p.rge), docs[p.id], p.charte_version_signee, version, jour)}
