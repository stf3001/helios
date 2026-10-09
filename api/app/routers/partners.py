from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.partner import Partner
from app.schemas.partner import PartnerApply
from app.services import regions

router = APIRouter(prefix="/partners", tags=["partners"])


def _to_public(p: Partner) -> dict:
    """Vue publique d'un partenaire (annuaire) — pas de SIRET/email exposés."""
    return {
        "id": p.id,
        "raison_sociale": p.raison_sociale,
        "rge": p.rge,
        "zones": p.zones or [],
        "metiers": p.metiers or [],
        "note_moyenne": p.note_moyenne,
    }


@router.get("")
async def list_partners(
    metier: str | None = None, zone: str | None = None, db: AsyncSession = Depends(get_db)
):
    """Annuaire public : partenaires actifs, filtrables par métier et zone (préfixe code postal)."""
    # Le filtre lit la zone demandee avec la MEME regle que l'ecriture. L'ancien
    # `startswith(zone[:2])` ratait la Corse : « 20000 » donne « 20 », et « 2A » ne
    # commence pas par « 20 ». Une zone illisible ne filtre rien plutot que de renvoyer
    # une erreur : c'est un parametre public et facultatif, pas une saisie engageante.
    departement_demande = None
    if zone:
        try:
            departement_demande = regions.normaliser_zone(zone)
        except regions.ZoneIllisible:
            return []

    stmt = select(Partner).where(Partner.statut == "actif").order_by(Partner.note_moyenne.desc().nullslast())
    rows = list(await db.scalars(stmt))
    result = []
    for p in rows:
        if metier and metier not in (p.metiers or []):
            continue
        if zone and departement_demande not in (p.zones or []):
            continue
        result.append(_to_public(p))
    return result


@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply(payload: PartnerApply, db: AsyncSession = Depends(get_db)):
    """Candidature partenaire — crée un partenaire en statut « candidat » (validation manuelle ensuite)."""
    # Les zones sont ramenees a des numeros de departement DES L'ECRITURE : `chat.py`
    # compare par egalite stricte au departement du visiteur, donc un partenaire ayant
    # saisi « 69001 » n'etait jamais propose. Le refus nomme la valeur fautive — une
    # zone qu'on laisserait tomber en silence, c'est un partenaire qui ne couvre plus
    # ce qu'il a declare, et il ne l'apprendrait qu'en ne recevant jamais de client.
    try:
        zones = regions.normaliser_zones(payload.zones)
    except regions.ZoneIllisible as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone « {e.valeur} » non reconnue : indiquez un numero de departement "
                   f"(13, 2A) ou un code postal (13100).",
        )

    partner = Partner(
        raison_sociale=payload.raison_sociale,
        siret=payload.siret,
        email=payload.email,
        rge=payload.rge,
        zones=zones,
        metiers=payload.metiers,
        statut="candidat",
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return {"id": partner.id, "statut": partner.statut,
            "message": "Candidature reçue. Nous revenons vers vous après vérification (RGE, décennale, Kbis…)."}
