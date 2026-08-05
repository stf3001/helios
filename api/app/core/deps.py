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
    """Garde les endpoints admin via un secret partagé (X-Admin-Token). Conservé pour les
    scripts et l'outillage en ligne de commande ; le back-office, lui, passe par
    `get_current_admin` (compte utilisateur + JWT)."""
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès admin refusé")


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authentifie un administrateur pour le back-office : même JWT que l'espace client,
    mais exige `users.is_admin`. Renvoie 403 (et non 404) pour rester explicite côté UI."""
    user = await get_current_user(credentials, db)
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux administrateurs")
    return user


async def require_admin_access(
    x_admin_token: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Garde des routes admin, acceptant DEUX voies d'accès :

    - `X-Admin-Token` : secret partagé, pour les scripts et l'outillage en ligne de commande ;
    - JWT d'un compte `is_admin` : pour le back-office.

    Renvoie le compte admin quand l'accès vient d'un utilisateur (permet de l'afficher et,
    plus tard, de tracer les accès), ou None pour un accès par secret partagé.
    """
    if x_admin_token and x_admin_token == settings.admin_token:
        return None
    if credentials is not None:
        user_id = decode_access_token(credentials.credentials)
        if user_id is not None:
            user = await db.get(User, uuid.UUID(user_id))
            if user is not None and user.is_admin:
                return user
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès admin refusé")
