"""Trois foyers de TEST pour vérifier « Les risques de ma commune » (phase 2), base de dev seulement.

Chacun a une maison dont le code postal mène à la commune à vérifier ; la commune se choisit
ensuite dans l'écran (c'est ce qu'on vérifie). Débroussaillement « je ne sais pas ».

IDENTIFIANTS DE TEST (base de développement uniquement, comme `demo@helios.fr` dans CLAUDE.md) :
les e-mails de `FOYERS`, mot de passe `MOT_DE_PASSE`.

Idempotent. Lancer depuis `api/` : `.venv/Scripts/python.exe -m scripts.seed_risques_demo`
"""
import asyncio

from sqlalchemy import select

from app.core.db import async_session
from app.core.security import hash_password
from app.models.house import House
from app.models.user import User
from app.services.completeness import compute_score

MOT_DE_PASSE = "Risques-Test-2026!"
FOYERS = {  # e-mail → (code postal, commune attendue)
    "risques-var@example.com": ("83680", "La Garde-Freinet — feux de forêt"),
    "risques-argiles@example.com": ("32000", "Auch — argiles"),
    "risques-creuse@example.com": ("23150", "Ahun — peu exposée"),
}


async def semer() -> None:
    async with async_session() as db:
        for email, (cp, _) in FOYERS.items():
            u = await db.scalar(select(User).where(User.email == email))
            if u is None:
                u = User(email=email, prenom="Test")
                db.add(u)
            u.password_hash, u.email_verified = hash_password(MOT_DE_PASSE), True
            await db.flush()
            h = await db.scalar(select(House).where(House.user_id == u.id))
            if h is None:
                h = House(user_id=u.id, code_postal=cp)
                db.add(h)
            h.code_postal, h.type_logement, h.statut, h.zone_old = cp, "maison", "proprietaire", "ne_sais_pas"
            h.code_insee = h.commune = None
            h.completeness_score = compute_score(h)
        await db.commit()
    print(f"{len(FOYERS)} foyers de test prêts.")


if __name__ == "__main__":
    asyncio.run(semer())
