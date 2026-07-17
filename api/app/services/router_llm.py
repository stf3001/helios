"""Routeur hybride local/API — doc 07 §5.

Classification par règles simples (le modèle local ne s'auto-évalue jamais) : le mode
public reste toujours local ; le mode connecté ne bascule vers l'API que si la fiche
est assez complète (score >= `rag_api_min_niveau`) ET que la question semble complexe
(longue ou mots-clés type "audit", "combien"...). Les plafonds de coût (jour/mois)
forcent un retour en local (« mode simplifié »), tout comme une API indisponible.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.services import anthropic_client, ollama_client
from app.services.anthropic_client import ApiUnavailable

Route = Literal["local", "api"]

_NIVEAUX_ELIGIBLES_API = {"prediagnostic_qualitatif", "preaudit_chiffre"}


def choose_route(*, mode: str, niveau: str | None, message: str) -> Route:
    if mode != "connecte":
        return "local"
    if niveau not in _NIVEAUX_ELIGIBLES_API:
        return "local"
    is_long = len(message) > settings.rag_api_long_message_chars
    has_keyword = any(kw in message.lower() for kw in settings.rag_api_keywords)
    return "api" if (is_long or has_keyword) else "local"


async def cost_caps_exceeded(db: AsyncSession, user_id: uuid.UUID) -> bool:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    daily_cost = await db.scalar(
        select(func.coalesce(func.sum(Message.estimated_cost_eur), 0.0))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id, Message.created_at >= today_start)
    )
    if daily_cost >= settings.llm_api_budget_daily_eur:
        return True

    monthly_cost = await db.scalar(
        select(func.coalesce(func.sum(Message.estimated_cost_eur), 0.0)).where(Message.created_at >= month_start)
    )
    return monthly_cost >= settings.llm_api_budget_monthly_eur


async def generate_route(
    db: AsyncSession,
    *,
    mode: str,
    niveau: str | None,
    message: str,
    user_id: uuid.UUID | None,
    prompt: str,
) -> tuple[Route, bool, AsyncIterator[str]]:
    """Décide local vs API et renvoie (route utilisée, mode_simplifie, flux de tokens)."""
    route = choose_route(mode=mode, niveau=niveau, message=message)

    if route == "api" and user_id is not None and await cost_caps_exceeded(db, user_id):
        route = "local"
        return "local", True, ollama_client.generate_stream(prompt)

    if route == "api":
        api_stream = anthropic_client.generate_stream(prompt)
        try:
            # Vérifie que l'API répond avant de s'engager (clé absente -> lève immédiatement) ;
            # on ne tente pas de rebasculer en local après le premier jeton envoyé au client.
            first_chunk = await api_stream.__anext__()
        except (ApiUnavailable, StopAsyncIteration):
            return "local", True, ollama_client.generate_stream(prompt)

        async def _rechain() -> AsyncIterator[str]:
            yield first_chunk
            async for chunk in api_stream:
                yield chunk

        return "api", False, _rechain()

    return "local", False, ollama_client.generate_stream(prompt)


def estimate_cost_eur(tokens: int | None) -> float | None:
    if tokens is None:
        return None
    return round((tokens / 1000) * settings.llm_price_per_1k_tokens_eur, 6)
