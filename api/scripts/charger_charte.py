"""Met en vigueur une version de la charte partenaire (mises en relation, lot 3).

Copie `kb/charte_partenaire.md` (sans son commentaire d'en-tête) dans la table `chartes`, sous
la version déclarée en tête (`version: v2`). La version en vigueur est la plus récente de la
table : dès qu'elle est chargée, tout partenaire qui n'a pas signé CETTE version sort des
propositions jusqu'à sa signature dans son espace.

À NE LANCER EN PRODUCTION QU'APRÈS RELECTURE DE STÉPHANE (`a_relire` dans le fichier). Sur la
base de développement, il sert à vérifier le lot avec les partenaires « Démo … ».

Refuse de remplacer une version déjà chargée : une version signée ne change plus de texte.
Lancer depuis `api/` : `.venv/Scripts/python.exe -m scripts.charger_charte`
"""

import asyncio
import re

from app.core.db import async_session
from app.models.partner import Charte
from app.services.agents_engine import _REPO_ROOT

FICHIER = _REPO_ROOT / "helios" / "kb" / "charte_partenaire.md"


def lire() -> tuple[str, str]:
    brut = FICHIER.read_text(encoding="utf-8")
    entete = re.match(r"\s*<!--(.*?)-->", brut, re.S)
    if entete is None:
        raise SystemExit("En-tête <!-- ... --> absent de la charte.")
    version = re.search(r"^version:\s*(\S+)", entete.group(1), re.M)
    if version is None:
        raise SystemExit("Version absente de l'en-tête de la charte.")
    return version.group(1), brut[entete.end():].strip()


async def charger() -> None:
    version, texte = lire()
    async with async_session() as db:
        if await db.get(Charte, version) is not None:
            raise SystemExit(f"La version {version} est déjà en vigueur : écrire une nouvelle version.")
        db.add(Charte(version=version, texte=texte))
        await db.commit()
    print(f"Charte {version} en vigueur ({len(texte)} caractères).")


if __name__ == "__main__":
    asyncio.run(charger())
