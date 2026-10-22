import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.house import House
from app.models.user import User
from app.schemas.house import UNITES_PAR_AUTRE_ENERGIE, HouseCreate, HouseOut, HouseUpdate
from datetime import date

from app.models.house_document import HouseDocument
from app.models.journal import JournalEntree
from app.services import fiche_equipements as fe
from app.services import parcours as pc
from app.services.completeness import block_scores, compute_score, niveau_for_score

router = APIRouter(prefix="/houses", tags=["houses"])


def _to_out(house: House, equipements: list[Equipement] = ()) -> HouseOut:
    fields = {c.name: getattr(house, c.name) for c in house.__table__.columns if c.name != "user_id"}
    return HouseOut(
        **fields,
        niveau=niveau_for_score(house.completeness_score),
        block_scores=block_scores(house),
        champs_verrouilles=fe.champs_verrouilles(equipements),
        parcours=pc.parcours(house),
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
    # Lot 8 : l'acheteur devient propriétaire — sa liste « Avant d'acheter » est archivée au
    # journal telle qu'elle était, puis vidée (le parcours « Avant d'acheter » disparaît).
    if house.statut == "en_achat" and champs.get("statut") == "proprietaire":
        lignes = pc.avant_achat(house)
        docs = {str(d.id): d.filename for d in await db.scalars(
            select(HouseDocument).where(HouseDocument.house_id == house.id))}
        db.add(JournalEntree(house_id=house.id, **pc.archive(lignes, docs, date.today())))
        house.avant_achat = None
    # Pré-audit lot 7 : l'unité doit aller avec le type — vérifié sur la fiche telle qu'elle sera.
    type_ = champs.get("conso_autre_energie_type", house.conso_autre_energie_type)
    unite = champs.get("conso_autre_energie_unite", house.conso_autre_energie_unite)
    if unite and unite not in UNITES_PAR_AUTRE_ENERGIE.get(type_, ()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Cette unité ne correspond pas à l'énergie choisie : choisissez-en une de la liste.")
    # Phase 2 : un autre code postal, c'est peut-être une autre commune — elle se rechoisit.
    if "code_postal" in champs and champs["code_postal"] != house.code_postal:
        house.code_insee = house.commune = None
    for field, value in champs.items():
        if field in ("zone_old", "chauffage_collectif") and value is None:
            value = "ne_sais_pas"  # colonne NOT NULL : « non renseigné » veut dire « je ne sais pas »
        setattr(house, field, value)
    house.completeness_score = compute_score(house)

    await db.commit()
    await db.refresh(house)
    return _to_out(house, equipements)
