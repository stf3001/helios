"""Mises en relation (leads) — doc 08. Consentement horodaté, cycle de statut, commission à la signature.

Garde-fous (doc 08 §2/§6) appliqués :
- un lead n'est créé qu'avec le consentement explicite du client (horodaté) ;
- le client peut retirer son consentement tant que le devis n'est pas signé ;
- lead immuable après SIGNÉ (traçabilité de la commission) ;
- la commission est calculée par le moteur déterministe (doc 08 §3), jamais saisie à la main.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.partner import Lead, Partner, Review
from app.models.user import User
from app.schemas.partner import LeadCreate, LeadStatusUpdate, ReviewCreate
from app.services import commission
from app.services.email import send_lead_notification

router = APIRouter(prefix="/leads", tags=["leads"])


async def _own_house(db: AsyncSession, user_id) -> House:
    house = await db.scalar(select(House).where(House.user_id == user_id))
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return house


async def _own_lead(db: AsyncSession, user_id, lead_id) -> Lead:
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    house = await db.get(House, lead.house_id)
    if house is None or house.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    return lead


def _to_out(lead: Lead, partner: Partner | None) -> dict:
    return {
        "id": lead.id,
        "partner": {"id": partner.id, "raison_sociale": partner.raison_sociale} if partner else None,
        "type": lead.type,
        "metier": lead.metier,
        "statut": lead.statut,
        "montant_travaux": lead.montant_travaux,
        "commission": float(lead.commission) if lead.commission is not None else None,
        "consent_client_at": lead.consent_client_at,
        "consent_retire_at": lead.consent_retire_at,
        "created_at": lead.created_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lead(payload: LeadCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Demande de mise en relation — exige le consentement explicite (doc 08 §6)."""
    if not payload.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le consentement explicite est requis pour transmettre votre demande.")
    house = await _own_house(db, user.id)

    partner = await db.get(Partner, payload.partner_id)
    if partner is None or partner.statut != "actif":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire indisponible")

    lead = Lead(
        house_id=house.id,
        partner_id=partner.id,
        audit_id=payload.audit_id,
        type=payload.type,
        metier=payload.metier,
        statut="transmis",  # créé puis immédiatement transmis au partenaire
        consent_client_at=datetime.now(timezone.utc),
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    await send_lead_notification(partner.email, partner.raison_sociale, lead.id)
    return _to_out(lead, partner)


@router.get("")
async def list_leads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    leads = list(await db.scalars(select(Lead).where(Lead.house_id == house.id).order_by(Lead.created_at.desc())))
    out = []
    for lead in leads:
        partner = await db.get(Partner, lead.partner_id)
        out.append(_to_out(lead, partner))
    return out


@router.post("/{lead_id}/withdraw")
async def withdraw_consent(lead_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Le client retire son consentement — possible tant que le devis n'est pas signé (doc 08 §6)."""
    lead = await _own_lead(db, user.id, lead_id)
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Le consentement ne peut plus être retiré après signature.")
    lead.consent_retire_at = datetime.now(timezone.utc)
    lead.statut = "perdu"
    lead.motif_perdu = "Consentement retiré par le client"
    await db.commit()
    return _to_out(lead, await db.get(Partner, lead.partner_id))


@router.patch("/{lead_id}/status")
async def update_status(
    lead_id, payload: LeadStatusUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Avance le lead dans son cycle. À SIGNÉ, la commission est calculée par le moteur déterministe.

    NB : en production ces transitions viendront de l'espace partenaire ; ici l'endpoint sert le suivi
    et la démo. Un lead SIGNÉ est immuable (doc 08 §2).
    """
    lead = await _own_lead(db, user.id, lead_id)
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead signé : immuable (traçabilité de la commission).")

    if payload.montant_travaux is not None:
        lead.montant_travaux = payload.montant_travaux
    if payload.statut == "perdu" and payload.motif_perdu:
        lead.motif_perdu = payload.motif_perdu

    lead.statut = payload.statut
    if payload.statut == "signe":
        lead.commission = commission.compute_commission(lead.metier, lead.montant_travaux)

    await db.commit()
    return _to_out(lead, await db.get(Partner, lead.partner_id))


@router.post("/{lead_id}/review", status_code=status.HTTP_201_CREATED)
async def review_partner(
    lead_id, payload: ReviewCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Notation post-chantier — obligatoire pour la qualité (doc 08 §4). Recalcule la note moyenne du partenaire."""
    lead = await _own_lead(db, user.id, lead_id)
    if lead.statut != "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "La notation intervient après signature du chantier.")
    if await db.scalar(select(Review).where(Review.lead_id == lead.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce chantier a déjà été noté.")

    db.add(Review(lead_id=lead.id, note=payload.note, commentaire=payload.commentaire))
    await db.flush()

    # Recalcule la note moyenne du partenaire sur l'ensemble de ses avis
    partner = await db.get(Partner, lead.partner_id)
    notes = list(await db.scalars(
        select(Review.note).join(Lead, Review.lead_id == Lead.id).where(Lead.partner_id == partner.id)
    ))
    partner.note_moyenne = round(sum(notes) / len(notes), 2) if notes else None
    await db.commit()
    return {"lead_id": lead.id, "note": payload.note, "partner_note_moyenne": partner.note_moyenne}
