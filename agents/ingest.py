"""Ingestion FAQ -> kb_documents/kb_chunks (doc 07 §2, jalon 3).

Ré-exécutable : upsert par (source, titre=question), pas de doublons.
Usage : depuis helios/, avec le venv de l'API (dépendances partagées) :
    api/.venv/Scripts/python.exe agents/ingest.py
"""
import asyncio
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from sqlalchemy import select  # noqa: E402

from app.core.db import async_session  # noqa: E402
from app.models.kb import KbChunk, KbDocument  # noqa: E402
from app.services.ollama_client import embed  # noqa: E402

FAQ_PATH = Path(__file__).resolve().parent.parent.parent / "05-FAQ-V1.md"
SOURCE = "faq_maison"

ENTRY_RE = re.compile(
    r"^### Q:\s*(?P<question>.+?)\s*\n"
    r"`(?P<meta>[^`]+)`\s*\n"
    r"R:\s*(?P<answer>.+?)(?=\n### Q:|\n## |\n---|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_meta(meta: str) -> dict:
    result: dict = {}
    for part in meta.split("|"):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        key, value = key.strip(), value.strip()
        result[key] = [t.strip() for t in value.split(",") if t.strip()] if key == "tags" else value
    return result


def parse_faq(text: str) -> list[dict]:
    return [
        {
            "question": m.group("question").strip(),
            "answer": m.group("answer").strip(),
            **parse_meta(m.group("meta")),
        }
        for m in ENTRY_RE.finditer(text)
    ]


async def ingest() -> None:
    entries = parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    today = date.today()

    added, updated = 0, 0
    async with async_session() as db:
        for entry in entries:
            question, answer = entry["question"], entry["answer"]
            content = f"Q: {question}\nR: {answer}"
            metadata = {
                "cat": entry.get("cat"),
                "tags": entry.get("tags", []),
                "verif": entry.get("verif"),
                "niveau_confiance": "officiel",
            }

            doc = await db.scalar(
                select(KbDocument).where(KbDocument.source == SOURCE, KbDocument.titre == question)
            )
            if doc is None:
                doc = KbDocument(source=SOURCE, titre=question, date_maj=today, statut="actif")
                db.add(doc)
                await db.flush()
                added += 1
            else:
                doc.date_maj = today
                updated += 1

            embedding = await embed(content)
            chunk = await db.scalar(select(KbChunk).where(KbChunk.document_id == doc.id))
            if chunk is None:
                db.add(KbChunk(document_id=doc.id, content=content, embedding=embedding, chunk_metadata=metadata))
            else:
                chunk.content = content
                chunk.embedding = embedding
                chunk.chunk_metadata = metadata

        await db.commit()

    print(f"Ingestion terminée : {added} documents créés, {updated} mis à jour, {len(entries)} chunks au total.")


if __name__ == "__main__":
    asyncio.run(ingest())
