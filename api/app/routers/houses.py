import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.house import House
from app.models.user import User
from app.schemas.house import HouseCreate, HouseOut, HouseUpdate
from app.services import fiche_equipements as fe
from app.services.completeness import block_scores, compute_score, niveau_for_score

router = APIRouter(prefix="/houses", tags=["houses"])


def _to_out(house: House, equipements: list[Equipement] = ()) -> HouseOut:
    fields = {c.name: getattr(house, c.name) for c in house.__table__.columns if c.name != "user_id"}
    return HouseOut(
        **fields,
        niveau=niveau_for_score(house.completeness_score),
        block_scores=block_scores(house),
        champs_verrouilles=fe.champs_verrouilles(equipements),
    )


async def _equipements(db: AsyncSession, house: House) -> list[Equipement]:
    return list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))


async def _get_own_house(db: AsyncSession, user_id: uuid.UUID) -> House | None:
    return await db.scalar(select(House).where(House.user_id == user_id))


@router.get("/me", response_model=HouseOut)
async def get_my_house(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _get_own_house(db, user.id)
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return _to_out(house, await _equipements(db, house))


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
    return _to_out(house)  # une fiche neuve n'a pas encore d'équipement


@router.patch("/me", response_model=HouseOut)
async def update_my_house(
    payload: HouseUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _get_own_house(db, user.id)
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")

    champs = payload.model_dump(exclude_unset=True)
    equipements = await _equipements(db, house)
    # Un champ que fixe un équipement du carnet se modifie là-bas (lot 7). La même valeur
    # renvoyée passe : la fiche enregistre son bloc entier, champs verrouillés compris.
    refuses = fe.refus_patch(house, equipements, champs)
    if refuses:
        noms = ", ".join(f"« {fe.LIBELLES_CHAMPS[c]} »" for c in refuses)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{noms} vient de vos équipements : modifiez-le dans « Mes équipements ».",
        )
    for field, value in champs.items():
        if field == "zone_old" and value is None:
            value = "ne_sais_pas"  # colonne NOT NULL : « non renseigné » veut dire « je ne sais pas »
        setattr(house, field, value)
    house.completeness_score = compute_score(house)

    await db.commit()
    await db.refresh(house)
    return _to_out(house, equipements)
