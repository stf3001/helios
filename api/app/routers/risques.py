"""La commune de la maison et ses risques (phase 2).

Le foyer choisit sa commune parmi celles de son code postal (API Découpage administratif) ; Hélios
ne demande jamais l'adresse. Les risques viennent de Géorisques, gardés 30 jours. Une panne ne
casse rien : la section répond « indisponible » et l'écran ne l'affiche pas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.routers.equipements import _own_house
from app.services import risques_affichage, risques_lecture
from app.services.entretien import table_courante, verifications

router = APIRouter(prefix="/houses/me", tags=["carnet"])


@router.get("/communes")
async def communes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    try:
        liste = await risques_lecture.communes_du_code_postal(house.code_postal)
    except Exception:  # noqa: BLE001
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "La liste des communes est momentanément indisponible.")
    return {"code_postal": house.code_postal, "communes": liste, "choisie": house.code_insee}


class Choix(BaseModel):
    code_insee: str = Field(pattern=r"^[0-9AB]{5}$")


@router.put("/commune")
async def choisir_commune(payload: Choix, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """La commune doit appartenir au code postal de la fiche : on le vérifie à la source."""
    house = await _own_house(db, user.id)
    try:
        liste = await risques_lecture.communes_du_code_postal(house.code_postal)
    except Exception:  # noqa: BLE001
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "La liste des communes est momentanément indisponible.")
    commune = next((c for c in liste if c["code_insee"] == payload.code_insee), None)
    if commune is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cette commune ne correspond pas à votre code postal.")
    house.code_insee, house.commune = commune["code_insee"], commune["nom"]
    await db.commit()
    return {"code_insee": house.code_insee, "commune": house.commune}


@router.get("/risques")
async def risques(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """`{disponible: false}` sans commune choisie ou si Géorisques ne répond pas (rien de collecté)."""
    house = await _own_house(db, user.id)
    if not house.code_insee:
        return {"disponible": False, "raison": "commune_absente"}
    ligne = await risques_lecture.risques_de_la_commune(db, house.code_insee)
    if ligne is None:
        return {"disponible": False, "raison": "indisponible"}
    verifs = verifications(table_courante()["taches"], house)
    return {"disponible": True, **risques_affichage.section(ligne, house, verifs)}
