"""Espace professionnel — Helios adapte ses conseils au contexte pro, propose le courtage pro.

Un client est « pro » s'il a un ProProfile. Réutilise le flux de courtage (courtage_client)
avec un potentiel d'économie plus élevé en pro.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.partner import Partner
from app.models.pro import ProProfile
from app.models.user import User
from app.schemas.pro import ProCourtageRequest, ProProfileIn
from app.services import courtage_client, pro_advisor

router = APIRouter(prefix="/pro", tags=["pro"])


def _to_out(p: ProProfile) -> dict:
    return {c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "user_id"}


async def _own_profile(db: AsyncSession, user_id) -> ProProfile | None:
    return await db.scalar(select(ProProfile).where(ProProfile.user_id == user_id))


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = await _own_profile(db, user.id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun profil professionnel")
    return _to_out(p)


@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(payload: ProProfileIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if await _own_profile(db, user.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un profil professionnel existe déjà")
    p = ProProfile(user_id=user.id, **payload.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _to_out(p)


@router.patch("/profile")
async def update_profile(payload: ProProfileIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = await _own_profile(db, user.id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun profil professionnel")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    p.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(p)
    return _to_out(p)


@router.get("/advice")
async def advice(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Conseils énergie adaptés au secteur et aux équipements du pro."""
    p = await _own_profile(db, user.id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Créez d'abord votre profil professionnel")
    return pro_advisor.advice(p)


@router.post("/courtage", status_code=status.HTTP_201_CREATED)
async def request_courtage(
    payload: ProCourtageRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Étude de courtage pro — exige le consentement explicite. Potentiel plus élevé qu'en résidentiel."""
    if not payload.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le consentement explicite est requis.")
    p = await _own_profile(db, user.id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Créez d'abord votre profil professionnel")

    courtier = await db.scalar(select(Partner).where(Partner.statut == "actif", Partner.metiers.any("courtage")))
    infos = {
        "fournisseur_actuel": p.fournisseur_actuel,
        "offre_actuelle": p.contrat_actuel,
        "conso_annuelle_kwh": p.conso_annuelle_kwh,
        "puissance_kva": p.puissance_kva,
        "montant_facture_annuelle_eur": payload.montant_facture_annuelle_eur,
    }
    estimation = courtage_client.estimation(None, infos, gain_pct=settings.courtage_gain_estime_pct_pro)
    opinion, favorable = courtage_client.helios_opinion(estimation)

    # NB : energy_studies.house_id est NOT NULL (résidentiel). Le courtage pro n'a pas de fiche maison :
    # on renvoie le résultat directement (persistance dédiée pro à ajouter si besoin de l'historiser).
    return {
        "type": "courtage_pro",
        "estimation": estimation,
        "helios_opinion": opinion,
        "favorable": favorable,
        "partenaire": courtier.raison_sociale if courtier else None,
        "comparateur_public": settings.energie_comparateur_public,
        "partner_link": (settings.courtage_partner_link or None) if favorable else None,
    }
