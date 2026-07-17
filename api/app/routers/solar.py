from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.house import House
from app.models.solar import SolarStudy
from app.models.user import User
from app.schemas.solar import SolarSimulateIn
from app.services import geocoding, pvgis, solar_engine
from app.services.geocoding import GeocodingError
from app.services.pvgis import PvgisError

router = APIRouter(prefix="/solar", tags=["solar"])


async def _resolve_location(payload: SolarSimulateIn, house: House | None) -> dict:
    if payload.lat is not None and payload.lon is not None:
        return {"lat": payload.lat, "lon": payload.lon, "label": None}
    if payload.adresse:
        return await geocoding.geocode(payload.adresse)
    if house is not None and house.code_postal:
        return await geocoding.geocode(house.code_postal)
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Fournissez une adresse ou des coordonnées GPS")


@router.post("/simulate")
async def simulate(
    payload: SolarSimulateIn,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Simulateur solaire — ouvert au public (résultats partiels), complet + stocké si connecté (doc 09 §1/§4)."""
    house = None
    if user:
        house = await db.scalar(select(House).where(House.user_id == user.id))

    # Les paramètres de la fiche Maison servent de valeurs par défaut en mode connecté
    orientation = payload.orientation or (house.orientation_toiture if house else None)
    pente = payload.pente if payload.pente is not None else (house.pente if house else None)
    ombrage = payload.ombrage or (house.ombrage if house else None)
    conso = house.conso_elec_kwh_an if house else payload.conso_kwh_an

    try:
        geo = await _resolve_location(payload, house)
        pvgis_result = await pvgis.simulate(
            lat=geo["lat"], lon=geo["lon"], orientation=orientation, pente=pente, ombrage=ombrage
        )
    except GeocodingError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PvgisError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Service de production solaire indisponible : {exc}") from exc

    params = {
        "gps": {"lat": geo["lat"], "lon": geo["lon"], "label": geo.get("label")},
        "orientation": orientation,
        "pente": pvgis_result["angle"],
        "ombrage": ombrage or "aucun",
        "surface_toit_m2": payload.surface_toit_m2,
    }

    # Mode public : production seule (l'aimant à inscription — pas de chiffrage économique ni de stockage)
    if user is None:
        production = {p: {"annual_kwh": d["annual_kwh"], "monthly_kwh": d["monthly_kwh"]}
                      for p, d in pvgis_result["by_power"].items()}
        return {
            "partiel": True,
            "params": params,
            "production": production,
            "message": "Créez un compte gratuit pour voir vos économies estimées, le temps de retour "
                       "et le scénario batterie — et pour qu'Helios commente votre projet.",
        }

    # Mode connecté : résultats complets + stockage
    scenarios = solar_engine.build_scenarios(pvgis_result, conso)
    study = SolarStudy(
        house_id=house.id if house else None,
        params=params,
        pvgis_result=pvgis_result,
        scenarios=scenarios,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)

    return {
        "partiel": False,
        "study_id": study.id,
        "params": params,
        "pvgis_result": pvgis_result,
        "scenarios": scenarios,
    }


@router.get("/studies")
async def list_studies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des études solaires de l'utilisateur (via sa fiche maison)."""
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(SolarStudy).where(SolarStudy.house_id == house.id).order_by(SolarStudy.created_at.desc())
    )
    return [
        {"id": s.id, "params": s.params, "scenarios": s.scenarios, "created_at": s.created_at} for s in rows
    ]
