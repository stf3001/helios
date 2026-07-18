import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.ratelimit import limiter
from app.core.security import create_access_token, hash_password, hash_token, new_raw_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "helios_refresh"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 86400,
        path="/api/auth",
    )


async def _issue_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
    raw = new_raw_token()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    return raw


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, payload: RegisterIn, response: Response, db: AsyncSession = Depends(get_db)):
    if not payload.consent_cgu:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'acceptation des CGU est requise")
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte existe déjà avec cet email")

    verify_raw = new_raw_token()
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        prenom=payload.prenom,
        consent_cgu_at=datetime.now(timezone.utc),
        email_verify_token_hash=hash_token(verify_raw),
        email_verify_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.email_verify_ttl_hours),
    )
    db.add(user)
    await db.flush()  # peuple user.id avant de créer le refresh token

    await send_verification_email(user.email, verify_raw)
    refresh_raw = await _issue_refresh_token(db, user.id)
    await db.commit()

    _set_refresh_cookie(response, refresh_raw)
    return TokenOut(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email_verify_token_hash == hash_token(token)))
    if user is None or user.email_verify_token_expires_at is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Lien de vérification invalide")
    if user.email_verify_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Lien de vérification expiré")

    user.email_verified = True
    user.email_verify_token_hash = None
    user.email_verify_token_expires_at = None
    await db.commit()
    return {"status": "ok"}


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginIn, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect")

    refresh_raw = await _issue_refresh_token(db, user.id)
    await db.commit()

    _set_refresh_cookie(response, refresh_raw)
    return TokenOut(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenOut)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée")
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw is None:
        raise unauthorized

    stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
    if stored is None or stored.revoked_at is not None or stored.expires_at < datetime.now(timezone.utc):
        raise unauthorized

    user = await db.get(User, stored.user_id)
    if user is None:
        raise unauthorized

    stored.revoked_at = datetime.now(timezone.utc)  # rotation : un refresh token ne sert qu'une fois
    refresh_raw = await _issue_refresh_token(db, user.id)
    await db.commit()

    _set_refresh_cookie(response, refresh_raw)
    return TokenOut(access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        stored = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            await db.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
