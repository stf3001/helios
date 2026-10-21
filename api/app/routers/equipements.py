"""Carnet de maison, lot 1 : les équipements, leurs suggestions depuis la fiche, les garanties.

Contrôles d'accès sur le modèle de `documents.py` : un identifiant appartenant à un autre
foyer répond 404, comme un identifiant qui n'existe pas — on ne confirme pas son existence.
L'âge est calculé ici, à la lecture, jamais stocké.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import MAX_EQUIPEMENTS_PAR_MAISON, Equipement
from app.models.house import House
from app.models.travaux import Travaux
from app.models.user import User
from app.schemas.equipement import EquipementCreate, EquipementUpdate, verifier_type
from app.services.garanties import age_ans, date_pose, garanties_maison
from app.services.suggestions_fiche import suggestions

router = APIRouter(prefix="/houses/me", tags=["carnet"])


async def _own_house(db: AsyncSession, user_id) -> House:
    house = await db.scalar(select(House).where(House.user_id == user_id))
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return house


async def _own_equipement(db: AsyncSession, house: House, equipement_id: uuid.UUID) -> Equipement:
    eq = await db.get(Equipement, equipement_id)
    if eq is None or eq.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Équipement introuvable")
    return eq


async def _verifier_travaux(db: AsyncSession, house: House, travaux_id: uuid.UUID | None) -> None:
    if travaux_id is None:
        return
    t = await db.get(Travaux, travaux_id)
    if t is None or t.house_id != house.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce chantier n'appartient pas à votre maison")


def _out(eq: Equipement, aujourd_hui: date) -> dict:
    sortie = {c.name: getattr(eq, c.name) for c in eq.__table__.columns}
    age, statut = age_ans(eq, aujourd_hui)
    sortie["age_ans"] = age
    sortie["age_statut"] = statut
    sortie["date_pose_retenue"] = date_pose(eq)[0]
    return sortie


@router.get("/equipements")
async def list_equipements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(Equipement).where(Equipement.house_id == house.id).order_by(Equipement.created_at)
    )
    aujourd_hui = date.today()
    return [_out(e, aujourd_hui) for e in rows]


@router.post("/equipements", status_code=status.HTTP_201_CREATED)
async def create_equipement(
    payload: EquipementCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _own_house(db, user.id)
    nb = await db.scalar(select(func.count()).select_from(Equipement).where(Equipement.house_id == house.id))
    if nb >= MAX_EQUIPEMENTS_PAR_MAISON:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Limite de {MAX_EQUIPEMENTS_PAR_MAISON} équipements atteinte — supprimez-en un pour en ajouter un.",
        )
    await _verifier_travaux(db, house, payload.travaux_id)
    eq = Equipement(house_id=house.id, **payload.model_dump())
    db.add(eq)
    await db.commit()
    await db.refresh(eq)
    return _out(eq, date.today())


@router.patch("/equipements/{equipement_id}")
async def update_equipement(
    equipement_id: uuid.UUID, payload: EquipementUpdate,
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    house = await _own_house(db, user.id)
    eq = await _own_equipement(db, house, equipement_id)
    champs = payload.model_dump(exclude_unset=True)
    if "travaux_id" in champs:
        await _verifier_travaux(db, house, champs["travaux_id"])
    try:
        verifier_type(champs.get("categorie", eq.categorie), champs.get("type", eq.type))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    for champ, valeur in champs.items():
        if champ in ("categorie", "type", "en_service") and valeur is None:
            continue  # colonnes NOT NULL : « null » ne veut rien dire ici
        setattr(eq, champ, valeur)
    await db.commit()
    await db.refresh(eq)
    return _out(eq, date.today())


@router.delete("/equipements/{equipement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipement(
    equipement_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _own_house(db, user.id)
    eq = await _own_equipement(db, house, equipement_id)
    await db.delete(eq)
    await db.commit()


@router.get("/equipements/suggestions")
async def list_suggestions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    return suggestions(house, equipements)


@router.get("/garanties")
async def list_garanties(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    travaux = list(await db.scalars(select(Travaux).where(Travaux.house_id == house.id)))
    return garanties_maison(equipements, travaux, date.today())
