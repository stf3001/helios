"""Mises en relation (leads). Consentement horodaté, cycle de statut.

Série 4, lot 1 (22/10/2026) : une mise en relation `travaux` est payée par le partenaire à PRIX
FIXE (`mer_prix_ht_eur`, figé sur le lead à sa création), quel que soit le montant des travaux.
Plus aucune commission n'est calculée sur un lead `travaux` ; `commission` reste en base pour
l'historique. Le courtage (`energie`) ne change pas.

Garde-fous :
- un lead n'est créé qu'avec le consentement explicite du client (horodaté) ;
- le foyer choisit parmi au plus 3 partenaires tirés au sort (`services/propositions.py`) ;
- un lead `travaux` : propriétaire ou acheteur, partenaire éligible à la création, pas de
  doublon, au plus 3 demandes actives par métier ;
- le client peut retirer son consentement tant que le devis n'est pas signé ;
- lead immuable après SIGNÉ.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.partner import Lead, Partner, Review
from app.models.user import User
from app.schemas.partner import LeadCreate, LeadStatusUpdate, ReviewCreate
from app.services import commission, propositions, regions
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
        "partner": {"id": partner.id, "raison_sociale": partner.raison_sociale,
                    "lien_interet": partner.lien_interet} if partner else None,
        "type": lead.type,
        "metier": lead.metier,
        "statut": lead.statut,
        "montant_travaux": lead.montant_travaux,
        # Ni commission ni prix au foyer : il ne paie rien, et le prix est le même pour tous.
        "consent_client_at": lead.consent_client_at,
        "consent_retire_at": lead.consent_retire_at,
        "created_at": lead.created_at,
    }


async def _nb_avis(db: AsyncSession) -> dict:
    rows = await db.execute(select(Lead.partner_id, func.count()).join(Review, Review.lead_id == Lead.id)
                            .group_by(Lead.partner_id))
    return dict(rows.all())


@router.get("/propositions")
async def get_propositions(metier: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Au plus 3 partenaires éligibles, TIRÉS AU SORT, dans un ordre aléatoire — jamais triés."""
    house = await _own_house(db, user.id)
    if metier not in propositions.METIERS_TRAVAUX:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Métier inconnu")
    departement = regions.departement_du_code_postal(house.code_postal or "")
    voit_demo = propositions.voit_les_demos(user.email)
    eligibles = [p for p in await db.scalars(select(Partner).where(Partner.statut == "actif"))
                 if propositions.eligible(p, departement, metier, voit_demo)]
    avis = await _nb_avis(db)
    tires = propositions.tirer(eligibles, settings.mer_nb_propositions)
    return {"metier": metier, "ordre": "tire_au_sort",
            "propositions": [propositions.proposition(p, avis.get(p.id, 0)) for p in tires]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lead(payload: LeadCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Demande de mise en relation — exige le consentement explicite (doc 08 §6)."""
    if not payload.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le consentement explicite est requis pour transmettre votre demande.")
    house = await _own_house(db, user.id)

    partner = await db.get(Partner, payload.partner_id)
    if partner is None or partner.statut != "actif":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire indisponible")
    prix_ht = None
    if payload.type == "travaux":
        actifs = list(await db.scalars(select(Lead).where(
            Lead.house_id == house.id, Lead.type == "travaux", Lead.statut.in_(propositions.STATUTS_ACTIFS))))
        refus = propositions.refus_creation(
            house.statut, payload.metier, partner, regions.departement_du_code_postal(house.code_postal or ""), actifs,
            propositions.voit_les_demos(user.email))
        if refus:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, refus)
        prix_ht = settings.mer_prix_ht_eur  # figé : un changement de prix ne touche pas les leads passés

    lead = Lead(
        house_id=house.id,
        partner_id=partner.id,
        audit_id=payload.audit_id,
        type=payload.type,
        metier=payload.metier,
        statut="transmis",  # créé puis immédiatement transmis au partenaire
        consent_client_at=datetime.now(timezone.utc),
        prix_ht=prix_ht,
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
    """Avance le lead dans son cycle. Aucune commission sur un lead `travaux` (prix fixe, figé à la
    création) ; le courtage (`energie`) garde son calcul.

    NB : en production ces transitions viendront de l'espace partenaire ; ici l'endpoint sert le suivi
    et la démo. Un lead SIGNÉ est immuable (doc 08 §2).
    """
    lead = await _own_lead(db, user.id, lead_id)
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead signé : immuable.")

    if payload.montant_travaux is not None:
        lead.montant_travaux = payload.montant_travaux
    if payload.statut == "perdu" and payload.motif_perdu:
        lead.motif_perdu = payload.motif_perdu

    lead.statut = payload.statut
    if payload.statut == "signe" and lead.type != "travaux":
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
