"""Carnet, lot 11 : les isolants d'un chantier (rubrique du carnet d'information du logement).

Contrôles d'accès comme `travaux.py` : un chantier ou un isolant d'un autre foyer répond 404.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.isolant import MAX_ISOLANTS_PAR_MAISON, Isolant
from app.models.user import User
from app.routers.equipements import _own_house
from app.routers.travaux import _own_travaux

router = APIRouter(prefix="/houses/me", tags=["carnet"])


class IsolantIn(BaseModel):
    """Tout est facultatif et déclaré ; le PATCH ne touche que ce qui est envoyé."""

    model_config = ConfigDict(extra="forbid")
    nature: str | None = Field(default=None, max_length=80)
    marque_reference: str | None = Field(default=None, max_length=120)
    resistance_thermique: float | None = Field(default=None, gt=0, le=50)
    conductivite: float | None = Field(default=None, gt=0, le=5)
    epaisseur_mm: float | None = Field(default=None, gt=0, le=2000)
    surface_m2: float | None = Field(default=None, gt=0, le=10000)
    interfaces: str | None = Field(default=None, max_length=2000)


def cols(i: Isolant) -> dict:
    return {c.name: getattr(i, c.name) for c in i.__table__.columns}


async def _own_isolant(db: AsyncSession, house, isolant_id: uuid.UUID) -> Isolant:
    i = await db.get(Isolant, isolant_id)
    if i is None or i.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Isolant introuvable")
    return i


@router.get("/isolants")
async def list_isolants(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    rows = await db.scalars(select(Isolant).where(Isolant.house_id == house.id).order_by(Isolant.created_at))
    return [cols(i) for i in rows]


@router.post("/travaux/{travaux_id}/isolants", status_code=status.HTTP_201_CREATED)
async def create_isolant(travaux_id: uuid.UUID, payload: IsolantIn, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    await _own_travaux(db, house, travaux_id)
    nb = await db.scalar(select(func.count()).select_from(Isolant).where(Isolant.house_id == house.id))
    if nb >= MAX_ISOLANTS_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limite de {MAX_ISOLANTS_PAR_MAISON} isolants atteinte.")
    i = Isolant(house_id=house.id, travaux_id=travaux_id, **payload.model_dump())
    db.add(i)
    await db.commit()
    await db.refresh(i)
    return cols(i)


@router.patch("/isolants/{isolant_id}")
async def update_isolant(isolant_id: uuid.UUID, payload: IsolantIn, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    i = await _own_isolant(db, house, isolant_id)
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        setattr(i, champ, valeur)
    await db.commit()
    await db.refresh(i)
    return cols(i)


@router.delete("/isolants/{isolant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_isolant(isolant_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    await db.delete(await _own_isolant(db, house, isolant_id))
    await db.commit()
