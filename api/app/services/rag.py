"""RAG au runtime — doc 07 §4 : recherche, seuil de pertinence, prompt avec constitution."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.kb import KbChunk, KbDocument

_CONSTITUTION_PATH = Path(__file__).resolve().parents[3] / "prompts" / "constitution-v0.1.md"
_constitution_text = _CONSTITUTION_PATH.read_text(encoding="utf-8") if _CONSTITUTION_PATH.exists() else ""


async def search_chunks(db: AsyncSession, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    distance = KbChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(KbChunk, KbDocument, distance.label("distance"))
        .join(KbDocument, KbChunk.document_id == KbDocument.id)
        .where(KbDocument.statut != "obsolete")
        .order_by(distance)
        .limit(top_k or settings.rag_top_k)
    )
    rows = (await db.execute(stmt)).all()
    return [{"chunk": chunk, "document": document, "score": 1 - dist} for chunk, document, dist in rows]


def best_score(results: list[dict]) -> float:
    return max((r["score"] for r in results), default=0.0)


def build_citations(results: list[dict]) -> list[dict]:
    if not results or best_score(results) < settings.rag_score_threshold:
        return []
    return [
        {
            "titre": r["document"].titre,
            "cat": r["chunk"].chunk_metadata.get("cat"),
            "score": round(r["score"], 3),
        }
        for r in results
    ]


def build_prompt(question: str, results: list[dict]) -> str:
    if not results or best_score(results) < settings.rag_score_threshold:
        sources_block = (
            "Aucune source fiable trouvée dans la base de connaissances pour cette question. "
            "Réponds prudemment, sans inventer de chiffre ni de règle."
        )
    else:
        sources_block = "\n\n".join(f"[Source {i + 1}] {r['chunk'].content}" for i, r in enumerate(results))

    return (
        f"{_constitution_text}\n\n"
        "---\n"
        "SOURCES DISPONIBLES (mode public/visiteur — ne cite que celles fournies ici, jamais d'autres) :\n"
        f"{sources_block}\n\n"
        "---\n"
        f"Question du visiteur : {question}\n"
        "Réponse d'Helios :"
    )
