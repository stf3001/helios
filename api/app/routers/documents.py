"""Documents de la fiche Maison (DPE, factures, photos…) — doc 02.

Stockage sur disque serveur (dossier `generated/house_docs/`, hors git), métadonnées en base.
Restreint aux formats courants (PDF/images) et à une taille max, pour la fiche de l'utilisateur.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.house import House
from app.models.house_document import DOC_TYPES, HouseDocument
from app.models.user import User

router = APIRouter(prefix="/houses/me/documents", tags=["documents"])

DOCS_DIR = Path(__file__).resolve().parents[2] / "generated" / "house_docs"
MAX_SIZE = 10 * 1024 * 1024  # 10 Mo
ALLOWED_CT = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic"}


async def _own_house(db: AsyncSession, user_id) -> House:
    house = await db.scalar(select(House).where(House.user_id == user_id))
    if house is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucune fiche maison — créez-la d'abord")
    return house


@router.get("")
async def list_documents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(HouseDocument).where(HouseDocument.house_id == house.id).order_by(HouseDocument.uploaded_at.desc())
    )
    return [
        {"id": d.id, "type": d.type, "filename": d.filename, "size": d.size, "uploaded_at": d.uploaded_at}
        for d in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if type not in DOC_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Type invalide (attendu : {', '.join(DOC_TYPES)})")
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Format non accepté (PDF ou image uniquement)")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Fichier trop volumineux (max 10 Mo)")

    house = await _own_house(db, user.id)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "").suffix[:10]
    stored = DOCS_DIR / f"{uuid.uuid4()}{ext}"
    stored.write_bytes(content)

    doc = HouseDocument(
        house_id=house.id, type=type, filename=file.filename or stored.name, path=str(stored), size=len(content)
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "type": doc.type, "filename": doc.filename, "size": doc.size, "uploaded_at": doc.uploaded_at}


async def _own_document(db: AsyncSession, user_id, doc_id) -> HouseDocument:
    doc = await db.get(HouseDocument, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    house = await db.get(House, doc.house_id)
    if house is None or house.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    return doc


@router.get("/{doc_id}")
async def download_document(doc_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    doc = await _own_document(db, user.id, doc_id)
    if not Path(doc.path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fichier indisponible")
    return FileResponse(doc.path, filename=doc.filename)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    doc = await _own_document(db, user.id, doc_id)
    Path(doc.path).unlink(missing_ok=True)
    await db.delete(doc)
    await db.commit()
