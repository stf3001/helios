"""Carnet de maison, lot 4 : le journal de la maison.

La lecture fusionne les entrées et les travaux du lot 1 (ceux-ci restent gérés par leur
propre route). Contrôles d'accès sur le modèle de `documents.py` : une entrée d'un autre
foyer répond 404 ; un équipement, une pièce ou un document lié doit être de la même maison
(400). Rien n'est créé ni mis hors service automatiquement, pas même pour un remplacement :
c'est l'écran qui le propose.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.journal import MAX_ENTREES_PAR_MAISON, JournalEntree
from app.models.piece import Piece
from app.models.travaux import Travaux
from app.models.user import User
from app.routers.equipements import _own_house
from app.schemas.journal import EntreeCreate, EntreeUpdate
from app.services.a_faire import journal_fusionne

router = APIRouter(prefix="/houses/me/journal", tags=["carnet"])

_LIENS = (("equipement_id", Equipement, "Cet équipement"), ("piece_id", Piece, "Cette pièce"),
          ("document_id", HouseDocument, "Ce document"))


async def verifier_liens(db: AsyncSession, house: House, champs: dict) -> None:
    for champ, modele, nom in _LIENS:
        cible_id = champs.get(champ)
        if cible_id is None:
            continue
        cible = await db.get(modele, cible_id)
        if cible is None or cible.house_id != house.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{nom} n'appartient pas à votre maison")


async def verifier_limite(db: AsyncSession, house: House) -> None:
    nb = await db.scalar(select(func.count()).select_from(JournalEntree).where(JournalEntree.house_id == house.id))
    if nb >= MAX_ENTREES_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Limite de {MAX_ENTREES_PAR_MAISON} entrées atteinte dans le journal.")


def cols(e: JournalEntree) -> dict:
    return {c.name: getattr(e, c.name) for c in e.__table__.columns}


async def _own_entree(db: AsyncSession, house: House, entree_id: uuid.UUID) -> JournalEntree:
    e = await db.get(JournalEntree, entree_id)
    if e is None or e.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrée introuvable")
    return e


@router.get("")
async def list_journal(equipement_id: uuid.UUID | None = Query(default=None),
                       user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    entrees = list(await db.scalars(select(JournalEntree).where(JournalEntree.house_id == house.id)))
    travaux = list(await db.scalars(select(Travaux).where(Travaux.house_id == house.id)))
    lies = frozenset()
    if equipement_id is not None:
        eq = await db.get(Equipement, equipement_id)
        lies = frozenset({eq.travaux_id}) if eq is not None and eq.house_id == house.id and eq.travaux_id else frozenset()
    return journal_fusionne(entrees, travaux, equipement_id, lies)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_entree(payload: EntreeCreate, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    await verifier_limite(db, house)
    champs = payload.model_dump()
    await verifier_liens(db, house, champs)
    e = JournalEntree(house_id=house.id, **champs)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return cols(e)


@router.patch("/{entree_id}")
async def update_entree(entree_id: uuid.UUID, payload: EntreeUpdate,
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    e = await _own_entree(db, house, entree_id)
    champs = payload.model_dump(exclude_unset=True)
    await verifier_liens(db, house, champs)
    for champ, valeur in champs.items():
        if valeur is None and champ in ("date", "type", "titre"):
            continue  # colonnes obligatoires
        setattr(e, champ, valeur)
    await db.commit()
    await db.refresh(e)
    return cols(e)


@router.delete("/{entree_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entree(entree_id: uuid.UUID, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    e = await _own_entree(db, house, entree_id)
    await db.delete(e)
    await db.commit()
