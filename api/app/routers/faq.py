"""FAQ publique — sert les entrées ingérées dans la base de connaissances (source `faq_maison`).

Même source que le RAG (doc 04) : la page /faq et le chat Helios puisent dans la même base,
plus de fichier statique à maintenir côté front.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.kb import KbChunk, KbDocument

router = APIRouter(prefix="/faq", tags=["faq"])

SOURCE = "faq_maison"


def _answer_from_content(content: str) -> str:
    """Le chunk est stocké sous la forme "Q: …\\nR: …" — on extrait la réponse."""
    marker = "\nR:"
    idx = content.find(marker)
    return content[idx + len(marker):].strip() if idx != -1 else content.strip()


@router.get("")
async def list_faq(db: AsyncSession = Depends(get_db)):
    """Toutes les entrées FAQ actives, avec catégorie et tags (depuis les métadonnées du chunk)."""
    stmt = (
        select(KbDocument, KbChunk)
        .join(KbChunk, KbChunk.document_id == KbDocument.id)
        .where(KbDocument.source == SOURCE, KbDocument.statut == "actif")
        .order_by(KbDocument.titre)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "question": doc.titre,
            "answer": _answer_from_content(chunk.content),
            "cat": (chunk.chunk_metadata or {}).get("cat"),
            "tags": (chunk.chunk_metadata or {}).get("tags", []),
        }
        for doc, chunk in rows
    ]
