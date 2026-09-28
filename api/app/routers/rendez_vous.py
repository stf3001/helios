"""Rendez-vous telephonique avec un conseiller — creneaux libres et reservation.

Reservable SANS COMPTE : c'est une porte d'entree, pas une recompense pour inscrits. Si
le visiteur est connecte, on rattache quand meme le rendez-vous a son compte.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_optional_user
from app.core.ratelimit import limiter
from app.models.rendez_vous import RendezVous
from app.models.user import User
from app.schemas.rendez_vous import RendezVousIn, RendezVousOut
from app.services import creneaux

router = APIRouter(prefix="/rendez-vous", tags=["rendez-vous"])


@router.get("/creneaux")
async def creneaux_libres(db: AsyncSession = Depends(get_db)):
    """La grille d'ouverture, moins ce qui est deja pris."""
    deja = await db.scalars(
        select(RendezVous.debut).where(RendezVous.statut != "annule")
    )
    libres = creneaux.libres(set(deja))
    return {
        "duree_min": settings.rdv_duree_min,
        "creneaux": [c.isoformat() for c in libres],
    }


@router.post("", response_model=RendezVousOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def reserver(
    request: Request,
    payload: RendezVousIn,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    # Le creneau doit tomber sur NOTRE grille : sans ce controle, on accepterait 3 h du
    # matin un dimanche, ou dans six mois.
    if not creneaux.est_proposable(payload.debut):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Ce créneau n'est pas proposé. Rechargez la page pour voir les disponibilités.")

    rdv = RendezVous(
        id=uuid.uuid4(),
        user_id=user.id if user else None,
        nom=payload.nom.strip(),
        telephone=payload.telephone.strip(),
        email=str(payload.email) if payload.email else None,
        sujet=payload.sujet,
        debut=payload.debut.astimezone(creneaux.FUSEAU),
        duree_min=settings.rdv_duree_min,
    )
    db.add(rdv)
    try:
        await db.commit()
    except IntegrityError:
        # L'index unique sur `debut` a parle : quelqu'un a pris le creneau entre
        # l'affichage de la page et le clic. C'est le seul verrou fiable — verifier
        # puis inserer laisserait passer deux reservations simultanees.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Ce créneau vient d'être pris. Choisissez-en un autre.")

    return RendezVousOut(id=str(rdv.id), debut=rdv.debut, duree_min=rdv.duree_min)
