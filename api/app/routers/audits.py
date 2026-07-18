from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.audit import Audit
from app.models.house import House
from app.models.user import User
from app.services import audit_engine, pdf_audit
from app.services.completeness import compute_score

router = APIRouter(prefix="/audits", tags=["audits"])


async def _own_house(db: AsyncSession, user_id) -> House:
    house = await db.scalar(select(House).where(House.user_id == user_id))
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return house


@router.post("", status_code=status.HTTP_201_CREATED)
async def generate_audit(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Génère un pré-audit déterministe — exige une fiche complète à ≥ 70 % (doc 02 / doc 07 §6)."""
    house = await _own_house(db, user.id)
    score = compute_score(house)
    if score < settings.audit_min_completeness:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Fiche trop incomplète ({score}%) — un pré-audit chiffré nécessite au moins "
            f"{settings.audit_min_completeness:.0f}% de complétude.",
        )

    result = audit_engine.run_audit(house)
    label = f"{house.type_logement or 'logement'} - {house.code_postal}"
    pdf_path = pdf_audit.build_pdf(result, house_label=label)

    audit = Audit(
        house_id=house.id,
        json_result=result,
        pdf_path=str(pdf_path),
        version_helios=result.get("version_helios"),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return {"id": audit.id, "created_at": audit.created_at, "result": result}


@router.get("")
async def list_audits(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(Audit).where(Audit.house_id == house.id).order_by(Audit.created_at.desc())
    )
    return [
        {"id": a.id, "created_at": a.created_at, "version_helios": a.version_helios, "result": a.json_result}
        for a in rows
    ]


async def _own_audit(db: AsyncSession, user_id, audit_id) -> Audit:
    audit = await db.get(Audit, audit_id)
    if audit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pré-audit introuvable")
    house = await db.get(House, audit.house_id)
    if house is None or house.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pré-audit introuvable")  # 404 plutôt que 403 (ne divulgue rien)
    return audit


@router.get("/{audit_id}")
async def get_audit(audit_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    audit = await _own_audit(db, user.id, audit_id)
    return {"id": audit.id, "created_at": audit.created_at, "result": audit.json_result}


@router.get("/{audit_id}/pdf")
async def get_audit_pdf(audit_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    audit = await _own_audit(db, user.id, audit_id)
    if not audit.pdf_path or not Path(audit.pdf_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF indisponible")
    return FileResponse(audit.pdf_path, media_type="application/pdf", filename=f"preaudit-helios-{audit_id}.pdf")
