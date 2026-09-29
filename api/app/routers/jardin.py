"""Le jardin nourricier — surface, recolte et temps d'entretien d'un potager.

PUBLIC ET SANS TRACE : rien n'est enregistre, pour personne. Le calcul est pur (aucune
I/O, aucun appel sortant), donc il n'y a ni cout a proteger ni resultat a conserver — a
la difference du potentiel hydrique, qui garde ses etudes dans l'espace client.

Le code postal est facultatif et ne sert qu'a nommer la zone de jardinage (nord ou sud).
Il n'est ni stocke ni transmis nulle part.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.user import User
from app.services import jardin

router = APIRouter(prefix="/jardin", tags=["jardin"])


class JardinIn(BaseModel):
    personnes: int = Field(default=2, ge=1, le=10)
    # Le temps est une CONTRAINTE D'ENTREE : le visiteur dit ce qu'il accepte d'y
    # passer, et le calcul repond ce que ce budget achete. Voir services/jardin.py.
    heures_jour: float = Field(default=1.0, ge=0.25, le=3.0)
    conduite: Literal["debutant", "rodee"] = "debutant"
    code_postal: str | None = Field(default=None, max_length=5)


@router.get("/reglages")
async def reglages():
    """Les bornes des curseurs, pour que l'ecran n'ait aucun chiffre en dur."""
    return {
        "personnes_max": settings.jardin_personnes_max,
        "heures_jour_min": settings.jardin_heures_jour_min,
        "heures_jour_max": settings.jardin_heures_jour_max,
        "heures_jour_defaut": settings.jardin_heures_jour_defaut,
        "conduites": [
            {"code": "debutant", "label": "Je débute",
             "detail": "Premier potager, on apprend en faisant."},
            {"code": "rodee", "label": "J'ai la main",
             "detail": "Paillage, arrosage automatique, successions de cultures."},
        ],
    }


@router.post("/calcul")
async def calcul(payload: JardinIn):
    try:
        return jardin.calcul(
            personnes=payload.personnes,
            heures_jour=payload.heures_jour,
            conduite=payload.conduite,
            code_postal=payload.code_postal,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/programme")
async def programme(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Le programme annuel de cultures — RESERVE AU COMPTE, et gratuit.

    C'est ce qu'on promet en echange de l'inscription : le calculateur du potager est
    public, le programme detaille ne l'est pas. Il n'y a rien a payer, rien a remplir de
    plus non plus — la zone se deduit du code postal deja donne dans la fiche Maison.
    """
    house = await db.scalar(select(House).where(House.user_id == user.id))
    return jardin.programme(house.code_postal if house else None)
