"""Espace énergie — doc 09 §2. Conseil niveau 1 (gratuit, sans tiers) + parcours SOBRY (niveau 2).

Garde-fous constitution (doc 09 §2) appliqués dans le code :
- une étude n'est JAMAIS créée sans consentement explicite ;
- l'avis d'Helios est rendu AVANT toute incitation, et peut être négatif ;
- le lien partenaire n'est proposé QUE si l'avis est favorable ;
- le comparateur public (energie-info.fr) est toujours mentionné ;
- le consentement est horodaté ; la décision reste au client.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.energy import EnergyStudy
from app.models.house import House
from app.models.user import User
from app.schemas.energy import CourtageRequest, StudyDecision, StudyRequest
from app.services import courtage_client, energy_advisor, sobry_client

router = APIRouter(prefix="/energy", tags=["energy"])


async def _own_house(db: AsyncSession, user_id) -> House:
    house = await db.scalar(select(House).where(House.user_id == user_id))
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return house


@router.get("/advice")
async def get_advice(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Conseil énergie niveau 1 — analyse de la fiche, sans tiers (doc 09 §2)."""
    house = await _own_house(db, user.id)
    return energy_advisor.advice(house)


@router.get("/spot-prices")
async def get_spot_prices():
    """Courbe de prix spot (API SOBRY si configurée, sinon courbe de démonstration étiquetée)."""
    return await sobry_client.spot_prices()


def _helios_opinion(estimation: dict) -> tuple[str, bool]:
    """Avis indépendant d'Helios sur l'estimation. Renvoie (texte, favorable)."""
    gain = estimation["gain_estime_pct"]
    compat = estimation["compatibilite"]
    comparateur = settings.energie_comparateur_public

    if compat == "prudence":
        return (
            "Votre profil se prête mal à un tarif dynamique (chauffage électrique peu pilotable) : "
            "risque de surcoût en pointe hivernale. Je vous déconseille cette offre en l'état. "
            f"Comparez librement les offres du marché sur le comparateur public indépendant {comparateur}.",
            False,
        )
    if gain < settings.sobry_seuil_gain_pct:
        return (
            f"L'économie estimée (~{gain}% ) est marginale : elle ne justifie pas de changer d'offre pour l'instant. "
            f"Restez sur votre contrat actuel et vérifiez d'autres offres sur {comparateur}.",
            False,
        )
    return (
        f"Votre profil est compatible et l'économie estimée (~{gain}% , à confirmer sur votre courbe de charge réelle) "
        "peut être intéressante. Ce n'est pas « la meilleure offre du marché » : comparez librement sur le comparateur "
        f"public indépendant {comparateur}. Pour information, HELIOS perçoit une commission de SOBRY si vous souscrivez — "
        "jamais de votre part ; mon avis reste indépendant.",
        True,
    )


@router.post("/study", status_code=status.HTTP_201_CREATED)
async def request_study(
    payload: StudyRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Demande d'étude SOBRY — exige le consentement explicite (doc 09 §2)."""
    if not payload.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le consentement explicite est requis pour lancer l'étude.")
    house = await _own_house(db, user.id)

    estimation = sobry_client.estimation(house, payload.pdl)
    opinion, favorable = _helios_opinion(estimation)

    study = EnergyStudy(
        house_id=house.id,
        pdl=payload.pdl,
        consent_at=datetime.now(timezone.utc),
        status="presentee",  # estimation reçue et présentée avec l'avis d'Helios
        result=estimation,
        helios_opinion=opinion,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)

    return {
        "id": study.id,
        "status": study.status,
        "estimation": estimation,
        "helios_opinion": opinion,
        "favorable": favorable,
        "comparateur_public": settings.energie_comparateur_public,
        # Garde-fou : le lien partenaire n'est proposé QUE si l'avis est favorable
        "partner_link": (settings.sobry_partner_link or None) if favorable else None,
    }


@router.post("/courtage", status_code=status.HTTP_201_CREATED)
async def request_courtage(
    payload: CourtageRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Demande d'étude de courtage d'énergie — Helios recueille le profil, transmet au partenaire
    courtier (avec consentement), reçoit et analyse le résultat, puis le présente (avis indépendant)."""
    if not payload.consent:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le consentement explicite est requis pour lancer l'étude.")
    house = await _own_house(db, user.id)

    # Partenaire courtier : un partenaire actif dont les métiers incluent "courtage" (à nommer plus tard)
    from app.models.partner import Partner
    courtier = await db.scalar(
        select(Partner).where(Partner.statut == "actif", Partner.metiers.any("courtage"))
    )

    estimation = courtage_client.estimation(house, payload.offre_actuelle)
    opinion, favorable = courtage_client.helios_opinion(estimation)

    study = EnergyStudy(
        house_id=house.id,
        partner_id=courtier.id if courtier else None,
        type="courtage",
        consent_at=datetime.now(timezone.utc),
        status="presentee",
        result=estimation,
        helios_opinion=opinion,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)

    return {
        "id": study.id,
        "type": "courtage",
        "status": study.status,
        "estimation": estimation,
        "helios_opinion": opinion,
        "favorable": favorable,
        "partenaire": courtier.raison_sociale if courtier else None,
        "comparateur_public": settings.energie_comparateur_public,
        # Garde-fou : lien partenaire proposé uniquement si l'avis est favorable
        "partner_link": (settings.courtage_partner_link or None) if favorable else None,
    }


@router.get("/studies")
async def list_studies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(EnergyStudy).where(EnergyStudy.house_id == house.id).order_by(EnergyStudy.created_at.desc())
    )
    return [
        {"id": s.id, "type": s.type, "status": s.status, "estimation": s.result,
         "helios_opinion": s.helios_opinion, "created_at": s.created_at}
        for s in rows
    ]


@router.post("/study/{study_id}/decision")
async def decide_study(
    study_id, payload: StudyDecision, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Le client tranche : souscrire (via le lien partenaire) ou décliner. La décision lui appartient."""
    study = await db.get(EnergyStudy, study_id)
    if study is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Étude introuvable")
    house = await db.get(House, study.house_id)
    if house is None or house.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Étude introuvable")

    study.status = payload.decision
    await db.commit()
    return {"id": study.id, "status": study.status}
