from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.autoconso import AutoconsoStudy
from app.models.user import User
from app.schemas.autoconso import AutoconsoSimulateIn
from app.services import enedis_client, geocoding, pvgis, autoconso_engine
from app.services.geocoding import GeocodingError
from app.services.pvgis import PvgisError

router = APIRouter(prefix="/autoconso", tags=["autoconso"])


@router.post("/simulate")
async def simulate(
    payload: AutoconsoSimulateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simulateur avancé (bêta) : PV + batterie physique et/ou virtuelle (MyLight) + tarif
    (fixe / SOBRY SoFlex / SOBRY SoCap), comparés à consommation réelle égale.

    Réservé aux utilisateurs connectés avec une fiche maison : la comparaison s'appuie sur
    une courbe de consommation (réelle Enedis à terme, simulée pour l'instant — toujours
    étiquetée) et sur une série de production PV heure par heure (PVGIS, réelle).
    """
    if (payload.battery_kwh is None) != (payload.battery_power_kw is None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "battery_kwh et battery_power_kw vont ensemble")

    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Complétez votre fiche maison avant de simuler")

    try:
        geo = await geocoding.geocode(house.code_postal)
        angle, aspect, loss = pvgis.resolve_angle_aspect_loss(house.orientation_toiture, house.pente, house.ombrage)
        prod_h = await pvgis.production_series_hourly(
            lat=geo["lat"], lon=geo["lon"], peakpower=payload.power_kwc, angle=angle, aspect=aspect, loss=loss
        )
    except GeocodingError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PvgisError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Service de production solaire indisponible : {exc}") from exc

    conso = await enedis_client.get_load_curve(house)
    conso_h = conso["hourly_kwh"]

    comparaison = autoconso_engine.compare_scenarios(
        conso_h,
        prod_h,
        battery_kwh=payload.battery_kwh,
        battery_power_kw=payload.battery_power_kw,
        mylight_power_kwc=payload.power_kwc if payload.mylight else None,
        tarif_modes=tuple(payload.tarif_modes),
    )

    result = {
        "power_kwc": payload.power_kwc,
        "production_annuelle_kwh": round(sum(prod_h)),
        "consommation": {"source": conso["source"], "annuelle_kwh": conso["annual_kwh"], "avertissement": conso["avertissement"]},
        "lignes": comparaison["lignes"],
    }

    # Conservée gratuitement dans l'espace client — et exploitable par Helios dans le chat.
    study = AutoconsoStudy(
        house_id=house.id,
        params=payload.model_dump(),
        result=result,
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)

    return {"study_id": study.id, **result}


@router.get("/studies")
async def list_studies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des simulations Autoconso de l'utilisateur, les plus récentes d'abord."""
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(AutoconsoStudy).where(AutoconsoStudy.house_id == house.id).order_by(AutoconsoStudy.created_at.desc())
    )
    return [{"id": s.id, "params": s.params, "result": s.result, "created_at": s.created_at} for s in rows]
