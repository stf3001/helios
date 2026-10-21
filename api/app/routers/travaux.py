"""Carnet de maison, lot 1 : les travaux réceptionnés, qui ouvrent les garanties de chantier.

Un document lié (facture, attestation d'assurance) doit appartenir à la même maison :
sinon 400, pour qu'on ne puisse pas rattacher — donc révéler — le papier d'un autre foyer.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.travaux import MAX_TRAVAUX_PAR_MAISON, Travaux
from app.models.user import User
from app.routers.equipements import _own_house
from app.schemas.travaux import TravauxCreate, TravauxUpdate
from app.services.garanties import fin_garanties_chantier, statut_garantie

router = APIRouter(prefix="/houses/me/travaux", tags=["carnet"])

_CHAMPS_DOCUMENT = ("facture_document_id", "attestation_assurance_document_id")


async def _own_travaux(db: AsyncSession, house: House, travaux_id: uuid.UUID) -> Travaux:
    t = await db.get(Travaux, travaux_id)
    if t is None or t.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chantier introuvable")
    return t


async def _verifier_documents(db: AsyncSession, house: House, champs: dict) -> None:
    for champ in _CHAMPS_DOCUMENT:
        doc_id = champs.get(champ)
        if doc_id is None:
            continue
        doc = await db.get(HouseDocument, doc_id)
        if doc is None or doc.house_id != house.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce document n'appartient pas à votre maison")


def _out(t: Travaux, aujourd_hui: date) -> dict:
    sortie = {c.name: getattr(t, c.name) for c in t.__table__.columns}
    sortie["garanties"] = [
        {**g, "statut": statut_garantie(g["fin"], aujourd_hui)}
        for g in (fin_garanties_chantier(t.date_reception) if t.date_reception else [])
    ]
    return sortie


@router.get("")
async def list_travaux(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(Travaux).where(Travaux.house_id == house.id)
        .order_by(Travaux.date_reception.desc().nulls_first(), Travaux.created_at.desc())
    )
    aujourd_hui = date.today()
    return [_out(t, aujourd_hui) for t in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_travaux(
    payload: TravauxCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _own_house(db, user.id)
    nb = await db.scalar(select(func.count()).select_from(Travaux).where(Travaux.house_id == house.id))
    if nb >= MAX_TRAVAUX_PAR_MAISON:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Limite de {MAX_TRAVAUX_PAR_MAISON} chantiers atteinte — supprimez-en un pour en ajouter un.",
        )
    champs = payload.model_dump()
    await _verifier_documents(db, house, champs)
    t = Travaux(house_id=house.id, **champs)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _out(t, date.today())


@router.patch("/{travaux_id}")
async def update_travaux(
    travaux_id: uuid.UUID, payload: TravauxUpdate,
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    house = await _own_house(db, user.id)
    t = await _own_travaux(db, house, travaux_id)
    champs = payload.model_dump(exclude_unset=True)
    await _verifier_documents(db, house, champs)
    for champ, valeur in champs.items():
        if champ == "nature" and not valeur:
            continue  # colonne obligatoire
        setattr(t, champ, valeur)
    await db.commit()
    await db.refresh(t)
    return _out(t, date.today())


@router.delete("/{travaux_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travaux(
    travaux_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    house = await _own_house(db, user.id)
    t = await _own_travaux(db, house, travaux_id)
    await db.delete(t)
    await db.commit()
