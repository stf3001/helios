from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.partner import Partner
from app.schemas.partner import PartnerApply

router = APIRouter(prefix="/partners", tags=["partners"])


def _to_public(p: Partner) -> dict:
    """Vue publique d'un partenaire (annuaire) — pas de SIRET/email exposés."""
    return {
        "id": p.id,
        "raison_sociale": p.raison_sociale,
        "rge": p.rge,
        "zones": p.zones or [],
        "metiers": p.metiers or [],
        "note_moyenne": p.note_moyenne,
    }


@router.get("")
async def list_partners(
    metier: str | None = None, zone: str | None = None, db: AsyncSession = Depends(get_db)
):
    """Annuaire public : partenaires actifs, filtrables par métier et zone (préfixe code postal)."""
    stmt = select(Partner).where(Partner.statut == "actif").order_by(Partner.note_moyenne.desc().nullslast())
    rows = list(await db.scalars(stmt))
    result = []
    for p in rows:
        if metier and metier not in (p.metiers or []):
            continue
        if zone and not any((z or "").startswith(zone[:2]) for z in (p.zones or [])):
            continue
        result.append(_to_public(p))
    return result


@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply(payload: PartnerApply, db: AsyncSession = Depends(get_db)):
    """Candidature partenaire — crée un partenaire en statut « candidat » (validation manuelle ensuite)."""
    partner = Partner(
        raison_sociale=payload.raison_sociale,
        siret=payload.siret,
        email=payload.email,
        rge=payload.rge,
        zones=payload.zones,
        metiers=payload.metiers,
        statut="candidat",
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return {"id": partner.id, "statut": partner.statut,
            "message": "Candidature reçue. Nous revenons vers vous après vérification (RGE, décennale, Kbis…)."}
