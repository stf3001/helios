"""Carnet, lot 8 : « Avant d'acheter » (acheteur) et la note au propriétaire (locataire).

La note n'est jamais envoyée : l'API rend un texte, le locataire le copie. La liste se coche
et se lie à un document déjà déposé (le dépôt passe par `documents.py`, ses limites comprises).
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house_document import HouseDocument
from app.models.user import User
from app.routers.entretien import _calcul
from app.routers.equipements import _own_house
from app.services import parcours as pc
from app.services.note_proprietaire import note

router = APIRouter(prefix="/houses/me", tags=["carnet"])


class LigneAchat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coche: bool | None = None
    document_id: uuid.UUID | None = None


@router.get("/avant-achat")
async def get_avant_achat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    return {"lignes": pc.avant_achat(house), "fiche": pc.FICHE_ACHAT}


@router.patch("/avant-achat/{item_id}")
async def patch_avant_achat(item_id: str, payload: LigneAchat, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    if item_id not in {i for i, _ in pc.items_applicables(house)}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ligne inconnue")
    champs = payload.model_dump(exclude_unset=True)
    if champs.get("document_id") is not None:
        doc = await db.get(HouseDocument, champs["document_id"])
        if doc is None or doc.house_id != house.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce document n'appartient pas à votre maison")
        champs["document_id"] = str(champs["document_id"])
    etat = dict(house.avant_achat or {})
    ligne = dict(etat.get(item_id) or {})
    for champ, valeur in champs.items():
        ligne[champ] = bool(valeur) if champ == "coche" else valeur
    etat[item_id] = ligne
    house.avant_achat = etat
    flag_modified(house, "avant_achat")
    await db.commit()
    return {"lignes": pc.avant_achat(house), "fiche": pc.FICHE_ACHAT}


@router.get("/note-proprietaire")
async def get_note_proprietaire(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    if not pc.parcours(house)["note_proprietaire"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La note au propriétaire est réservée aux locataires.")
    c = await _calcul(db, house)
    en_service = [e for e in c["equipements"] if e.en_service]
    return {"texte": note(c["echeances"], en_service, date.today())}
