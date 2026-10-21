"""Carnet de maison, lot 3 : les échéances d'entretien du foyer connecté.

Calcul seul : ni écran, ni rappel, ni e-mail (lot 4 et après). Le journal n'existant pas
encore, `derniers_faits` est vide — la référence est la date de pose, puis l'année.
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.user import User
from app.routers.equipements import _own_house
from app.services.entretien import echeances, table_courante, verifications

router = APIRouter(prefix="/houses/me/entretien", tags=["carnet"])


@router.get("")
async def get_entretien(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    table = table_courante()
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    return {
        "version": table["version"],
        "avertissement": table["avertissement"],
        "taches_validees": len(table["taches"]),
        # L'écran du lot 4 en a besoin pour dire « calendrier en préparation » plutôt que « rien à faire ».
        "table_vide": not table["taches"],
        "echeances": echeances(equipements, table["taches"], {}, date.today(), maison=house),
        # Sans date : « Vérifiez si votre terrain est concerné » quand la fiche dit « ne sais pas ».
        "verifications": verifications(table["taches"], house),
    }
