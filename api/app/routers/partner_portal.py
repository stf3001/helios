"""Espace partenaire — doc 04. Le partenaire se connecte, voit ses leads et fait avancer les statuts.

C'est ici que se fait la vraie transition de statut d'un lead (côté client, c'était une démo).
Mises en relation à prix fixe (série 4, lot 1) : aucune commission sur un lead `travaux`, le prix
est figé à la création (`prix_ht`) ; le courtage (`energie`) garde son calcul.

Lot 2 : le partenaire lit le dossier transmis (`GET /partner/leads/{id}`), figé au consentement,
avec son score expliqué ligne par ligne, les créneaux en tête et les coordonnées — en lecture
seule. Après un retrait de consentement, il ne reste rien à lire.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_partner
from app.core.security import create_partner_token, verify_password
from app.models.house import House
from app.models.partner import Lead, Partner
from app.routers.leads import LEAD_DOCS_DIR
from app.schemas.partner import LeadStatusUpdate
from app.services import commission

# Le partenaire n'appelle que parce que le foyer l'a demandé, dans les créneaux qu'il a donnés.
RAPPEL_LEGAL = ("Ce foyer a demandé à être contacté au sujet de ce projet. Appelez-le uniquement dans les "
                "créneaux indiqués : le démarchage téléphonique est interdit pour les travaux de rénovation "
                "énergétique (art. L. 223-1 du code de la consommation, loi n° 2020-901). Sans téléphone, "
                "écrivez-lui.")

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
            "prix_ht": float(lead.prix_ht) if lead.prix_ht is not None else None,
            "commission": float(lead.commission) if lead.commission is not None else None,  # historique, courtage
            "consent_retire": lead.consent_retire_at is not None,
            "score": lead.score,
            "created_at": lead.created_at,
        })
    return out


async def _lead_du_partenaire(db: AsyncSession, partner: Partner, lead_id) -> Lead:
    lead = await db.get(Lead, lead_id)
    if lead is None or lead.partner_id != partner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    return lead


@router.get("/leads/{lead_id}")
async def lead_detail(lead_id, partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Le dossier transmis, tel qu'il a été figé au consentement : créneaux en tête."""
    lead = await _lead_du_partenaire(db, partner, lead_id)
    return {
        "id": lead.id, "metier": lead.metier, "statut": lead.statut, "created_at": lead.created_at,
        "consent_client_at": lead.consent_client_at, "consent_retire": lead.consent_retire_at is not None,
        "prix_ht": float(lead.prix_ht) if lead.prix_ht is not None else None,
        "creneaux": lead.creneaux or [],
        "contact": {"nom": lead.contact_nom, "telephone": lead.contact_telephone, "email": lead.contact_email},
        "message": lead.message,
        "score": lead.score, "score_detail": lead.score_detail or [],
        "dossier": lead.dossier,
        "rappel_legal": RAPPEL_LEGAL,
    }


@router.get("/leads/{lead_id}/documents/{doc_id}")
async def lead_document(lead_id, doc_id, partner: Partner = Depends(get_current_partner),
                        db: AsyncSession = Depends(get_db)):
    """La COPIE faite au consentement — jamais le document de la maison lui-même."""
    lead = await _lead_du_partenaire(db, partner, lead_id)
    docs = {d["id"]: d for d in ((lead.dossier or {}).get("documents") or [])}
    doc = docs.get(str(doc_id))
    copies = list((LEAD_DOCS_DIR / str(lead.id)).glob(f"{doc_id}.*")) if doc else []
    if not copies:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    return FileResponse(copies[0], filename=doc["filename"])


@router.patch("/leads/{lead_id}/status")
async def advance_lead(
    lead_id, payload: LeadStatusUpdate,
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if lead is None or lead.partner_id != partner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead signé : immuable.")
    if lead.consent_retire_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Consentement retiré par le client : lead inexploitable.")

    if payload.montant_travaux is not None:
        lead.montant_travaux = payload.montant_travaux
    if payload.statut == "perdu" and payload.motif_perdu:
        lead.motif_perdu = payload.motif_perdu

    lead.statut = payload.statut
    if payload.statut == "signe" and lead.type != "travaux":
        lead.commission = commission.compute_commission(lead.metier, lead.montant_travaux)
    await db.commit()
    return {"id": lead.id, "statut": lead.statut, "commission": float(lead.commission) if lead.commission else None}
