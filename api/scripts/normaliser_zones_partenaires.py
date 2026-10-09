r"""Ramene les `partners.zones` deja en base a des numeros de departement.

    .venv\Scripts\python.exe -m scripts.normaliser_zones_partenaires [--appliquer]

Sans `--appliquer`, le script n'ecrit RIEN : il montre ce qu'il changerait. C'est voulu —
il touche le champ qui decide quels partenaires Helios nomme a un client.

Pourquoi ce script existe : le champ etait rempli en texte libre, et le formulaire public
proposait meme des codes postaux en exemple, alors que `routers/chat.py` compare la zone
au departement du visiteur par egalite STRICTE. Un partenaire ayant declare « 69001 »
n'etait donc jamais propose. La normalisation se fait desormais a l'ecriture
(`POST /partners/apply`) ; ce script rattrape les lignes anterieures.

Les zones illisibles ne sont PAS supprimees : elles sont signalees et laissees en place.
Effacer en masse une zone qu'on ne sait pas lire reviendrait a retirer un partenaire de
sa region sans que personne ne le sache.
"""

import asyncio
import sys

from sqlalchemy import select

from app.core.db import async_session
from app.models.partner import Partner
from app.services import regions


async def normaliser(appliquer: bool) -> None:
    async with async_session() as db:
        partenaires = list(await db.scalars(select(Partner).order_by(Partner.raison_sociale)))

        a_changer: list[tuple[Partner, list[str], list[str]]] = []
        illisibles: list[tuple[str, str]] = []

        for p in partenaires:
            avant = list(p.zones or [])
            apres: list[str] = []
            for zone in avant:
                try:
                    dept = regions.normaliser_zone(zone)
                except regions.ZoneIllisible:
                    illisibles.append((p.raison_sociale, zone))
                    apres.append(zone)      # on garde tel quel, voir l'en-tete
                    continue
                if dept not in apres:
                    apres.append(dept)
            if apres != avant:
                a_changer.append((p, avant, apres))

        print(f"{len(partenaires)} partenaires lus, {len(a_changer)} a corriger.")
        for p, avant, apres in a_changer:
            print(f"  {p.raison_sociale:28} {avant} -> {apres}")

        if illisibles:
            print(f"\n{len(illisibles)} zone(s) illisible(s), LAISSEES EN PLACE :")
            for raison, zone in illisibles:
                print(f"  {raison:28} {zone!r}")

        if not appliquer:
            print("\n(simulation — relancer avec --appliquer pour ecrire)")
            return

        for p, _, apres in a_changer:
            p.zones = apres
        await db.commit()
        print(f"\n{len(a_changer)} partenaire(s) mis a jour.")


if __name__ == "__main__":
    asyncio.run(normaliser("--appliquer" in sys.argv))
