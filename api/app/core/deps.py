import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import decode_access_token, decode_partner_token
from app.models.partner import Partner
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Non authentifié")
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise unauthorized
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Comme get_current_user, mais renvoie None au lieu de lever 401 — pour les
    endpoints utilisables en mode public (visiteur) ET en mode connecté (doc 07 §4)."""
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None
    return await db.get(User, uuid.UUID(user_id))


async def get_current_partner(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """Authentifie un partenaire (jeton type=partner) pour l'espace partenaire."""
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Non authentifié")
    if credentials is None:
        raise unauthorized
    partner_id = decode_partner_token(credentials.credentials)
    if partner_id is None:
        raise unauthorized
    partner = await db.get(Partner, uuid.UUID(partner_id))
    if partner is None or partner.statut != "actif":
        raise unauthorized
    return partner


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Garde les endpoints admin via un secret partagé (X-Admin-Token). Simple, suffisant en v1."""
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès admin refusé")
