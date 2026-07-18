"""Ingestion FAQ -> RAG (doc 07 §2, jalon 3).

Conservé pour compatibilité : délègue désormais au framework d'agents (agents_engine, J10).
Équivalent à `run_agents.py crawl`. Usage depuis helios/ avec le venv de l'API :
    api/.venv/Scripts/python.exe agents/ingest.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from app.core.db import async_session  # noqa: E402
from app.services import agents_engine  # noqa: E402


async def ingest() -> None:
    async with async_session() as db:
        for result in await agents_engine.run_crawler(db):
            print("Ingestion :", result)


if __name__ == "__main__":
    asyncio.run(ingest())
