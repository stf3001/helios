"""Carnet, lot 10 : ce que coûte la maison, et ce que les travaux changeraient.

`GET /houses/me/cout` assemble (`services/cout_maison.py`) ; `GET/PUT /houses/me/charges`
tient les charges déclarées. Le dernier pré-audit et les études du simulateur sont lus tels
qu'ils ont été stockés : rien n'est recalculé ici.
"""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.audit import Audit
from app.models.charges import ChargesMaison
from app.models.journal import JournalEntree
from app.models.simulateur import SimulateurStudy
from app.models.user import User
from app.routers.equipements import _own_house
from app.services.cout_maison import cout_possession, effet_travaux

router = APIRouter(prefix="/houses/me", tags=["carnet"])

MAX_ETUDES_AFFICHEES = 5
_MONTANT = Field(default=None, ge=0, le=1_000_000)


class Charges(BaseModel):
    """Tout est facultatif : `null` = non renseigné. Le PUT remplace l'ensemble."""

    model_config = ConfigDict(extra="forbid")
    assurance_eur_an: float | None = _MONTANT
    taxe_fonciere_eur_an: float | None = _MONTANT
    charges_copro_eur_an: float | None = _MONTANT
    eau_eur_an: float | None = _MONTANT
    autre_eur_an: float | None = _MONTANT
    autre_libelle: str | None = Field(default=None, max_length=80)


def _out(c: ChargesMaison | None) -> dict:
    return {champ: getattr(c, champ) if c else None for champ in Charges.model_fields}


@router.get("/charges")
async def get_charges(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    return _out(await db.scalar(select(ChargesMaison).where(ChargesMaison.house_id == house.id)))


@router.put("/charges")
async def put_charges(payload: Charges, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    c = await db.scalar(select(ChargesMaison).where(ChargesMaison.house_id == house.id))
    if c is None:
        c = ChargesMaison(house_id=house.id)
        db.add(c)
    for champ, valeur in payload.model_dump().items():
        setattr(c, champ, valeur)
    await db.commit()
    await db.refresh(c)
    return _out(c)


@router.get("/cout")
async def get_cout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    charges = await db.scalar(select(ChargesMaison).where(ChargesMaison.house_id == house.id))
    journal = list(await db.scalars(select(JournalEntree).where(JournalEntree.house_id == house.id)))
    audit = await db.scalar(select(Audit).where(Audit.house_id == house.id).order_by(Audit.created_at.desc()).limit(1))
    etudes = list(await db.scalars(select(SimulateurStudy).where(SimulateurStudy.house_id == house.id)
                                   .order_by(SimulateurStudy.created_at.desc()).limit(MAX_ETUDES_AFFICHEES)))
    return {
        **cout_possession(house, charges, journal, date.today()),
        "effet_travaux": effet_travaux(
            (audit.json_result, audit.created_at, audit.id) if audit else None,
            [(e.resultat, e.created_at, e.id, e.nom) for e in etudes],
        ),
    }
