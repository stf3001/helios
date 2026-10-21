"""Carnet de maison, lot 2 : les pièces, leurs émetteurs et le résumé calculé.

Contrôles d'accès sur le modèle de `documents.py` : une pièce ou un émetteur d'un autre
foyer répond 404. Un émetteur ne peut viser qu'un équipement de la même maison (400).
La photo d'une pièce passe par l'envoi de documents (`documents.py`, champ `piece_id`).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.piece import MAX_EMETTEURS_PAR_PIECE, MAX_PIECES_PAR_MAISON, Emetteur, Piece
from app.models.user import User
from app.routers.equipements import _own_house
from app.schemas.piece import Demarrage, EmetteurCreate, EmetteurUpdate, PieceCreate, PieceUpdate
from app.services.pieces import resume_pieces

router = APIRouter(prefix="/houses/me/pieces", tags=["carnet"])

# Colonnes NOT NULL : un `null` envoyé en modification ne veut rien dire, on l'ignore.
_NON_NULS_PIECE = ("nom", "type", "niveau", "chauffee", "ordre")
_NON_NULS_EMETTEUR = ("type", "nombre")


async def _own_piece(db: AsyncSession, house: House, piece_id: uuid.UUID) -> Piece:
    p = await db.get(Piece, piece_id)
    if p is None or p.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pièce introuvable")
    return p


async def _own_emetteur(db: AsyncSession, piece: Piece, emetteur_id: uuid.UUID) -> Emetteur:
    e = await db.get(Emetteur, emetteur_id)
    if e is None or e.piece_id != piece.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Émetteur introuvable")
    return e


async def _verifier_equipement(db: AsyncSession, house: House, equipement_id: uuid.UUID | None) -> None:
    if equipement_id is None:
        return
    eq = await db.get(Equipement, equipement_id)
    if eq is None or eq.house_id != house.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cet équipement n'appartient pas à votre maison")


def _normaliser(e: Emetteur) -> None:
    """Le robinet thermostatique n'existe que sur un radiateur à eau."""
    if e.type != "radiateur_eau":
        e.robinet_thermostatique = None


def _cols(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


async def _charger(db: AsyncSession, house: House):
    pieces = list(await db.scalars(
        select(Piece).where(Piece.house_id == house.id).order_by(Piece.niveau, Piece.ordre, Piece.created_at)
    ))
    ids = [p.id for p in pieces]
    emetteurs = list(await db.scalars(
        select(Emetteur).where(Emetteur.piece_id.in_(ids)).order_by(Emetteur.created_at)
    )) if ids else []
    return pieces, emetteurs


@router.get("")
async def list_pieces(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    pieces, emetteurs = await _charger(db, house)
    photos = {
        d.piece_id: {"id": d.id, "filename": d.filename}
        for d in await db.scalars(
            select(HouseDocument).where(HouseDocument.house_id == house.id, HouseDocument.piece_id.is_not(None))
        )
    }
    return [
        {**_cols(p), "emetteurs": [_cols(e) for e in emetteurs if e.piece_id == p.id], "photo": photos.get(p.id)}
        for p in pieces
    ]


@router.get("/resume")
async def get_resume(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    pieces, emetteurs = await _charger(db, house)
    return resume_pieces(house, pieces, emetteurs)


async def _nb_pieces(db: AsyncSession, house: House) -> int:
    return await db.scalar(select(func.count()).select_from(Piece).where(Piece.house_id == house.id))


@router.post("/demarrage", status_code=status.HTTP_201_CREATED)
async def demarrage(payload: Demarrage, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    if await _nb_pieces(db, house):
        raise HTTPException(status.HTTP_409_CONFLICT, "Votre maison a déjà des pièces : ajoutez-les une par une.")
    for i, p in enumerate(payload.pieces):
        champs = {k: v for k, v in p.model_dump().items() if v is not None}
        champs.setdefault("ordre", i)
        db.add(Piece(house_id=house.id, **champs))
    await db.commit()
    return {"crees": len(payload.pieces)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_piece(payload: PieceCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    nb = await _nb_pieces(db, house)
    if nb >= MAX_PIECES_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Limite de {MAX_PIECES_PAR_MAISON} pièces atteinte — supprimez-en une pour en ajouter une.")
    champs = {k: v for k, v in payload.model_dump().items() if v is not None}
    champs.setdefault("ordre", nb)
    p = Piece(house_id=house.id, **champs)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return {**_cols(p), "emetteurs": [], "photo": None}


@router.patch("/{piece_id}")
async def update_piece(piece_id: uuid.UUID, payload: PieceUpdate,
                       user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_piece(db, house, piece_id)
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        if valeur is None and champ in _NON_NULS_PIECE:
            continue
        setattr(p, champ, valeur)
    await db.commit()
    await db.refresh(p)
    return _cols(p)


@router.delete("/{piece_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_piece(piece_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Les émetteurs partent avec la pièce (cascade) ; sa photo reste dans les papiers."""
    house = await _own_house(db, user.id)
    p = await _own_piece(db, house, piece_id)
    await db.delete(p)
    await db.commit()


@router.post("/{piece_id}/emetteurs", status_code=status.HTTP_201_CREATED)
async def create_emetteur(piece_id: uuid.UUID, payload: EmetteurCreate,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_piece(db, house, piece_id)
    nb = await db.scalar(select(func.count()).select_from(Emetteur).where(Emetteur.piece_id == p.id))
    if nb >= MAX_EMETTEURS_PAR_PIECE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Limite de {MAX_EMETTEURS_PAR_PIECE} lignes d'émetteurs par pièce atteinte.")
    await _verifier_equipement(db, house, payload.equipement_id)
    e = Emetteur(piece_id=p.id, **{k: v for k, v in payload.model_dump().items() if v is not None})
    _normaliser(e)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return _cols(e)


@router.patch("/{piece_id}/emetteurs/{emetteur_id}")
async def update_emetteur(piece_id: uuid.UUID, emetteur_id: uuid.UUID, payload: EmetteurUpdate,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_piece(db, house, piece_id)
    e = await _own_emetteur(db, p, emetteur_id)
    champs = payload.model_dump(exclude_unset=True)
    if "equipement_id" in champs:
        await _verifier_equipement(db, house, champs["equipement_id"])
    for champ, valeur in champs.items():
        if valeur is None and champ in _NON_NULS_EMETTEUR:
            continue
        setattr(e, champ, valeur)
    _normaliser(e)
    await db.commit()
    await db.refresh(e)
    return _cols(e)


@router.delete("/{piece_id}/emetteurs/{emetteur_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emetteur(piece_id: uuid.UUID, emetteur_id: uuid.UUID,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_piece(db, house, piece_id)
    e = await _own_emetteur(db, p, emetteur_id)
    await db.delete(e)
    await db.commit()
