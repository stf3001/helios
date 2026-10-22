"""Partenaires de DÉMONSTRATION pour vérifier les mises en relation (point 60 de TODO.md).

Décision de Stéphane du 22/10/2026 : aucun partenaire réel n'a de charte datée, donc aucun
foyer ne reçoit de proposition. Plutôt que de dater la charte d'un partenaire réel — ce qui
n'appartient qu'à lui —, on crée des partenaires CLAIREMENT FICTIFS :

- nommés « Démo … » ;
- `demo = True` : visibles des seuls comptes de `mer_comptes_demo` (le compte de démo), jamais
  dans l'annuaire public, jamais nommés par le chat, jamais proposés à un autre foyer ;
- charte datée, actifs, dans le Var (83, le département du compte de démo) ;
- le premier a un accès au portail partenaire, pour lire le dossier transmis.

IDENTIFIANTS DE TEST (base de développement uniquement, comme `demo@helios.fr` dans CLAUDE.md) :
portail partenaire `partenaire-demo@helios.fr`, mot de passe `MOT_DE_PASSE_PORTAIL` ci-dessous.

Idempotent : relancé, il remet les mêmes valeurs. Lancer depuis `api/` :
`.venv/Scripts/python.exe -m scripts.seed_partenaires_demo`
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import async_session
from app.core.security import hash_password
from app.models.partner import Partner

CHARTE = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
EMAIL_PORTAIL = "partenaire-demo@helios.fr"
MOT_DE_PASSE_PORTAIL = "Demo-Partenaire-2026!"

#: raison sociale -> métiers. Quatre partenaires sur les trois mêmes métiers : chacun en a
#: quatre éligibles, donc un vrai tirage de trois.
DEMOS: dict[str, tuple[str, ...]] = {
    "Démo Isolation Azur": ("isolation", "solaire", "pac"),
    "Démo Soleil du Var": ("isolation", "solaire", "pac"),
    "Démo Thermique Maures": ("isolation", "solaire", "pac"),
    "Démo Combles Provence": ("isolation", "solaire", "pac"),
}


async def semer() -> None:
    async with async_session() as db:
        for i, (nom, metiers) in enumerate(DEMOS.items()):
            p = await db.scalar(select(Partner).where(Partner.raison_sociale == nom))
            if p is None:
                p = Partner(raison_sociale=nom)
                db.add(p)
            p.demo, p.statut, p.charte_signee_at = True, "actif", CHARTE
            p.zones, p.metiers, p.rge = ["83"], list(metiers), True
            p.lien_interet = None
            if i == 0:
                p.email, p.password_hash = EMAIL_PORTAIL, hash_password(MOT_DE_PASSE_PORTAIL)
        await db.commit()
    print(f"{len(DEMOS)} partenaires de démonstration prêts (visibles du seul compte de démo).")


if __name__ == "__main__":
    asyncio.run(semer())
