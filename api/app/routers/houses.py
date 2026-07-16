import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.user import User
from app.schemas.house import HouseCreate, HouseOut, HouseUpdate
from app.services.completeness import block_scores, compute_score, niveau_for_score

router = APIRouter(prefix="/houses", tags=["houses"])


def _to_out(house: House) -> HouseOut:
    fields = {c.name: getattr(house, c.name) for c in house.__table__.columns if c.name != "user_id"}
    return HouseOut(
        **fields,
        niveau=niveau_for_score(house.completeness_score),
        block_scores=block_scores(house),
    )


async def _get_own_house(db: AsyncSession, user_id: uuid.UUID) -> House | None:
    return await db.scalar(select(House).where(House.user_id == user_id))


@router.get("/me", response_model=HouseOut)
async def get_my_house(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _get_own_house(db, user.id)
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return _to_out(house)


@router.post("/me", response_model=HouseOut, status_code=status.HTTP_201_CREATED)
async def create_my_house(
    payload: HouseCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    if await _get_own_house(db, user.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Une fiche maison existe déjà pour ce compte")

    house = House(user_id=user.id, code_postal=payload.code_postal)
    house.completeness_score = compute_score(house)
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return _to_out(house)


@router.patch("/me", response_model=HouseOut)
async def update_my_house(
    payload: HouseUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _get_own_house(db, user.id)
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(house, field, value)
    house.completeness_score = compute_score(house)

    await db.commit()
    await db.refresh(house)
    return _to_out(house)
