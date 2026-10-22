"""Collecte de la vigilance météo pour toute la France (phase 2).

    .venv/Scripts/python.exe -m scripts.collecter_vigilance            # au plus toutes les heures
    .venv/Scripts/python.exe -m scripts.collecter_vigilance --force    # même si la dernière est récente
    .venv/Scripts/python.exe -m scripts.collecter_vigilance --fixture tests/fixtures/meteofrance/carte_simulee.json

Sans `METEOFRANCE_API_KEY`, la collecte réelle ne fait rien (« dormant »). `--fixture` charge un
produit « carte » ENREGISTRÉ, sans réseau : base de développement seulement, pour vérifier
l'affichage. À la mise en ligne, le planificateur du serveur lancera la première forme chaque heure.
"""
import argparse
import asyncio
import json
from pathlib import Path

from app.core.db import async_session
from app.services import meteofrance_vigilance as mf
from app.services import vigilance_lecture


async def main(force: bool, fixture: str | None) -> None:
    collecter = None
    if fixture:
        carte = json.loads(Path(fixture).read_text(encoding="utf-8"))

        async def collecter():
            return mf.normaliser_carte(carte)
        force = True
    async with async_session() as db:
        print(await vigilance_lecture.collecter_si_besoin(db, force=force, collecter=collecter))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    p.add_argument("--fixture")
    a = p.parse_args()
    asyncio.run(main(a.force, a.fixture))
