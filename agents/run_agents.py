"""Lance les agents HELIOS (doc 10 J10).

Usage (depuis helios/, avec le venv de l'API) :
    api/.venv/Scripts/python.exe agents/run_agents.py crawl   # ingère/rafraîchit les sources RAG
    api/.venv/Scripts/python.exe agents/run_agents.py veille  # repère les contenus périmés

À planifier (cron / tâche Windows) une fois en production.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from app.core.db import async_session  # noqa: E402
from app.services import agents_engine  # noqa: E402


async def main(command: str) -> None:
    async with async_session() as db:
        if command == "crawl":
            for r in await agents_engine.run_crawler(db):
                print(r)
        elif command == "veille":
            print(await agents_engine.run_veille(db))
        else:
            print("Commande inconnue. Utilisez : crawl | veille")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "crawl"))
