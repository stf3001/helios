"""Espace partenaire — doc 04. Le partenaire se connecte, voit ses leads et fait avancer les statuts.

C'est ici que se fait la vraie transition de statut d'un lead (côté client, c'était une démo).
À SIGNÉ, la commission est calculée par le moteur déterministe (doc 08 §3).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_partner
from app.core.security import create_partner_token, verify_password
from app.models.house import House
from app.models.partner import Lead, Partner
from app.schemas.partner import LeadStatusUpdate
from app.services import commission

router = APIRouter(prefix="/partner", tags=["partner"])


class PartnerLogin(BaseModel):
    email: str
    password: str


@router.post("/login")
async def partner_login(payload: PartnerLogin, db: AsyncSession = Depends(get_db)):
    partner = await db.scalar(select(Partner).where(Partner.email == payload.email))
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    if partner is None or not partner.password_hash or partner.statut != "actif":
        raise invalid
    if not verify_password(payload.password, partner.password_hash):
        raise invalid
    return {"access_token": create_partner_token(str(partner.id)), "raison_sociale": partner.raison_sociale}


@router.get("/leads")
async def my_leads(partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Leads reçus par ce partenaire (données client minimales : ville via code postal, pas de PII inutile)."""
    leads = list(await db.scalars(
        select(Lead).where(Lead.partner_id == partner.id).order_by(Lead.created_at.desc())
    ))
    out = []
    for lead in leads:
        house = await db.get(House, lead.house_id)
        out.append({
            "id": lead.id,
            "type": lead.type,
            "metier": lead.metier,
            "statut": lead.statut,
            "code_postal": house.code_postal if house else None,
            "montant_travaux": lead.montant_travaux,
            "commission": float(lead.commission) if lead.commission is not None else None,
            "consent_retire": lead.consent_retire_at is not None,
            "created_at": lead.created_at,
        })
    return out


@router.patch("/leads/{lead_id}/status")
async def advance_lead(
    lead_id, payload: LeadStatusUpdate,
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if lead is None or lead.partner_id != partner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead signé : immuable (traçabilité de la commission).")
    if lead.consent_retire_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Consentement retiré par le client : lead inexploitable.")

    if payload.montant_travaux is not None:
        lead.montant_travaux = payload.montant_travaux
    if payload.statut == "perdu" and payload.motif_perdu:
        lead.motif_perdu = payload.motif_perdu

    lead.statut = payload.statut
    if payload.statut == "signe":
        lead.commission = commission.compute_commission(lead.metier, lead.montant_travaux)
    await db.commit()
    return {"id": lead.id, "statut": lead.statut, "commission": float(lead.commission) if lead.commission else None}
