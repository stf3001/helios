import logging
from collections.abc import AsyncIterator

import anthropic

from app.core.config import settings

logger = logging.getLogger("helios.anthropic")


class ApiUnavailable(Exception):
    """Clé absente, appel réseau impossible ou erreur API — déclenche le fallback local (doc 07 §5)."""


async def generate_stream(system: str, user_content: str) -> AsyncIterator[str]:
    """Génère la réponse token par token via l'API Claude (doc 10 §1).

    `system` (la constitution, strictement identique à chaque appel) est envoyé séparément du
    contenu utilisateur et marqué `cache_control` : Anthropic met en cache ce préfixe stable
    entre les appels (5 min glissantes), ce qui réduit coût et latence sur la partie répétitive
    du prompt — le contenu variable (fiche foyer, études, question) reste hors cache. Sans effet
    (ignoré silencieusement par l'API, jamais d'erreur) si le préfixe est sous le seuil minimum
    de tokens du modèle — voir doc Anthropic « prompt caching » : 4096 tokens pour Haiku 4.5.

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
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
            final = await stream.get_final_message()
            logger.info(
                "usage tokens=%s cache_write=%s cache_read=%s",
                final.usage.input_tokens,
                final.usage.cache_creation_input_tokens,
                final.usage.cache_read_input_tokens,
            )
    except anthropic.APIError as exc:
        raise ApiUnavailable(str(exc)) from exc
