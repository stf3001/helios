"""Compte & RGPD — doc 10 sécurité : export et suppression de compte, gestion des consentements.

- Export : portabilité (toutes les données de l'utilisateur en JSON).
- Suppression : droit à l'effacement — supprime le compte et toutes ses données liées (+ fichiers).
- Consentements : le client active/retire son consentement à la mise en relation partenaires.
"""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.audit import Audit
from app.models.conversation import Conversation, Message
from app.models.energy import EnergyStudy
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.partner import Lead, Review
from app.models.refresh_token import RefreshToken
from app.models.solar import SolarStudy
from app.models.user import User

router = APIRouter(prefix="/account", tags=["account"])


def _serialize(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@router.get("/export")
async def export_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Export RGPD : toutes les données personnelles de l'utilisateur (portabilité)."""
    data: dict = {"user": {k: v for k, v in _serialize(user).items() if k not in ("password_hash", "email_verify_token_hash")}}
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house:
        data["house"] = _serialize(house)
        data["documents"] = [_serialize(d) for d in await db.scalars(
            select(HouseDocument).where(HouseDocument.house_id == house.id))]
        data["audits"] = [_serialize(a) for a in await db.scalars(select(Audit).where(Audit.house_id == house.id))]
        data["solar_studies"] = [_serialize(s) for s in await db.scalars(
            select(SolarStudy).where(SolarStudy.house_id == house.id))]
        data["energy_studies"] = [_serialize(e) for e in await db.scalars(
            select(EnergyStudy).where(EnergyStudy.house_id == house.id))]
        data["leads"] = [_serialize(l) for l in await db.scalars(select(Lead).where(Lead.house_id == house.id))]
    convs = list(await db.scalars(select(Conversation).where(Conversation.user_id == user.id)))
    data["conversations"] = [_serialize(c) for c in convs]
    return data


class Consents(BaseModel):
    consent_leads: bool


@router.get("/consents")
async def get_consents(user: User = Depends(get_current_user)):
    return {
        "consent_cgu": user.consent_cgu_at is not None,
        "consent_leads": user.consent_leads_at is not None,
        "consent_leads_at": user.consent_leads_at,
    }


@router.patch("/consents")
async def update_consents(payload: Consents, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.consent_leads_at = datetime.now(timezone.utc) if payload.consent_leads else None
    await db.commit()
    return {"consent_leads": user.consent_leads_at is not None}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Droit à l'effacement : supprime le compte et toutes les données liées (+ fichiers sur disque)."""
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house:
        # fichiers documents sur disque
        for doc in await db.scalars(select(HouseDocument).where(HouseDocument.house_id == house.id)):
            Path(doc.path).unlink(missing_ok=True)
        # avis liés aux leads de la maison
        lead_ids = [l.id for l in await db.scalars(select(Lead).where(Lead.house_id == house.id))]
        if lead_ids:
            await db.execute(delete(Review).where(Review.lead_id.in_(lead_ids)))
        await db.execute(delete(Lead).where(Lead.house_id == house.id))
        await db.execute(delete(EnergyStudy).where(EnergyStudy.house_id == house.id))
        await db.execute(delete(SolarStudy).where(SolarStudy.house_id == house.id))
        await db.execute(delete(Audit).where(Audit.house_id == house.id))
        await db.execute(delete(HouseDocument).where(HouseDocument.house_id == house.id))
    # conversations + messages
    conv_ids = [c.id for c in await db.scalars(select(Conversation).where(Conversation.user_id == user.id))]
    if conv_ids:
        await db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
        await db.execute(delete(Conversation).where(Conversation.user_id == user.id))
    if house:
        await db.execute(delete(House).where(House.id == house.id))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()
