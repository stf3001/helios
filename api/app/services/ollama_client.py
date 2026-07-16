import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import settings


async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(base_url=settings.ollama_url, timeout=60) as client:
        res = await client.post("/api/embeddings", json={"model": settings.embed_model, "prompt": text})
        res.raise_for_status()
        return res.json()["embedding"]


async def generate_stream(prompt: str) -> AsyncIterator[str]:
    """Génère la réponse token par token via Ollama (mode local, doc 10 §1)."""
    async with httpx.AsyncClient(base_url=settings.ollama_url, timeout=None) as client:
        async with client.stream(
            "POST", "/api/generate", json={"model": settings.ollama_model, "prompt": prompt, "stream": True}
        ) as res:
            res.raise_for_status()
            async for line in res.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("response"):
                    yield data["response"]
                if data.get("done"):
                    break
