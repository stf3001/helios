"""Documents de la fiche Maison (DPE, factures, photos…) — doc 02.

Stockage sur disque serveur (dossier `generated/house_docs/`, hors git), métadonnées en base.
Restreint aux formats courants (PDF/images) et à une taille max, pour la fiche de l'utilisateur.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import func, select
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
MAX_DOCUMENTS_PAR_MAISON = 6  # limite volontaire, à revoir plus tard (doc produit)
MAX_EXTRACT_CHARS = 6000  # texte transmis à Helios pour son avis — assez pour un devis, pas plus


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
    nb_documents = await db.scalar(
        select(func.count()).select_from(HouseDocument).where(HouseDocument.house_id == house.id)
    )
    if nb_documents >= MAX_DOCUMENTS_PAR_MAISON:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Limite de {MAX_DOCUMENTS_PAR_MAISON} documents atteinte — supprimez-en un pour en ajouter un nouveau.",
        )

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


@router.get("/{doc_id}/extract")
async def extract_document_text(doc_id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Texte extrait d'un document PDF (devis, DPE…), pour préparer une question à Helios.

    Ne fonctionne que pour les PDF (une photo n'a pas de texte à extraire). Le texte n'est
    JAMAIS analysé ni chiffré ici — il sert seulement de matière première à une question
    posée ensuite par l'utilisateur dans le chat ; Helios répond alors comme à toute question,
    sans jamais garantir un chiffre à partir d'un document qu'il ne peut pas vérifier.
    """
    doc = await _own_document(db, user.id, doc_id)
    path = Path(doc.path)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fichier indisponible")
    if path.suffix.lower() != ".pdf":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Extraction disponible uniquement pour les PDF")

    try:
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "PDF illisible ou protégé") from exc

    text = text.strip()
    if not text:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Aucun texte extrait (probablement un PDF scanné en image) — décrivez le document à Helios directement.",
        )
    tronque = len(text) > MAX_EXTRACT_CHARS
    return {"text": text[:MAX_EXTRACT_CHARS], "tronque": tronque, "filename": doc.filename}
