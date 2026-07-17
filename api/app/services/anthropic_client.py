from collections.abc import AsyncIterator

import anthropic

from app.core.config import settings


class ApiUnavailable(Exception):
    """Clé absente, appel réseau impossible ou erreur API — déclenche le fallback local (doc 07 §5)."""


async def generate_stream(prompt: str) -> AsyncIterator[str]:
    """Génère la réponse token par token via l'API Claude (doc 10 §1).

    Ne tente jamais d'appel réseau si aucune clé n'est configurée : lève immédiatement
    pour laisser le routeur (`router_llm.py`) basculer en local sans délai.
    """
    if not settings.llm_api_key:
        raise ApiUnavailable("LLM_API_KEY non configurée")

    client = anthropic.AsyncAnthropic(api_key=settings.llm_api_key)
    try:
        async with client.messages.stream(
            model=settings.llm_api_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError as exc:
        raise ApiUnavailable(str(exc)) from exc
