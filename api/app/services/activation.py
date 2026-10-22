"""Lien d'activation d'un compte partenaire (mises en relation, lot 3).

Pas d'e-mail : l'administration copie le lien et le transmet elle-même. Le jeton n'est stocké
que haché (SHA-256), il expire après `mer_activation_jours` jours et ne sert qu'une fois.
Créer un nouveau lien invalide les précédents non utilisés.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.partner import Partner, PartnerActivation

CHEMIN = "/partenaire/activer"


def hacher(jeton: str) -> str:
    return hashlib.sha256(jeton.encode()).hexdigest()


def utilisable(activation: PartnerActivation | None, maintenant: datetime) -> bool:
    return activation is not None and activation.utilise_le is None and maintenant <= activation.expire_le


async def creer(db: AsyncSession, partner: Partner, maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    await db.execute(update(PartnerActivation)
                     .where(PartnerActivation.partner_id == partner.id, PartnerActivation.utilise_le.is_(None))
                     .values(expire_le=maintenant - timedelta(seconds=1)))
    jeton = secrets.token_urlsafe(32)
    expire = maintenant + timedelta(days=settings.mer_activation_jours)
    db.add(PartnerActivation(partner_id=partner.id, jeton_hash=hacher(jeton), expire_le=expire))
    return {"lien": f"{CHEMIN}?jeton={jeton}", "expire_le": expire}


async def trouver(db: AsyncSession, jeton: str) -> PartnerActivation | None:
    return await db.scalar(select(PartnerActivation).where(PartnerActivation.jeton_hash == hacher(jeton)))
