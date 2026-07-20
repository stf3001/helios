"""Potentiel hydrique — production d'eau atmosphérique (Hydrolia).

Ouvert au public (résultat sans compte) ; stocké si connecté. Réutilise le moteur water_engine
(tables constructeur Hydrolia, gitignorées) avec repli simplifié si absentes.
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.house import House
from app.models.user import User
from app.models.water import WaterStudy
from app.services import water_engine

router = APIRouter(prefix="/water", tags=["water"])


class WaterSimulateIn(BaseModel):
    ville: str
    modele: Literal["20L", "50L", "100L", "250L", "500L", "1000L"] = "20L"


@router.get("/cities")
async def cities():
    """Villes disponibles pour l'estimation (climat moyen)."""
    return water_engine.available_cities()


@router.post("/simulate")
async def simulate(
    payload: WaterSimulateIn,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = water_engine.water_potential(payload.ville, payload.modele)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    if user is None:
        return {"partiel": False, "result": result}  # le calcul eau est déjà entièrement public

    house = await db.scalar(select(House).where(House.user_id == user.id))
    study = WaterStudy(
        house_id=house.id if house else None,
        params={"ville": payload.ville, "modele": payload.modele},
        result=result,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    return {"partiel": False, "study_id": study.id, "result": result}


@router.get("/studies")
async def list_studies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(WaterStudy).where(WaterStudy.house_id == house.id).order_by(WaterStudy.created_at.desc())
    )
    return [{"id": s.id, "params": s.params, "result": s.result, "created_at": s.created_at} for s in rows]
