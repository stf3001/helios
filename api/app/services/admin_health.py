"""État des services dont dépend Helios — diagnostic du back-office.

Motivation concrète : plusieurs pannes vécues (« Helios indisponible », pages vides) venaient
simplement d'un service arrêté. Cet écran répond en un coup d'œil à « qu'est-ce qui est tombé ? ».

Principe : on ne PING que ce qui est gratuit et local/public. Pour Anthropic, on ne consomme
jamais de crédit juste pour un test : on rapporte l'état de configuration, pas un appel réel.
"""

import asyncio
import time

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

_TIMEOUT = 4.0


def _ok(nom: str, etat: str, detail: str, ms: float | None = None) -> dict:
    return {"nom": nom, "etat": etat, "detail": detail, "latence_ms": round(ms) if ms is not None else None}


async def _postgres(db: AsyncSession) -> dict:
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        return _ok("PostgreSQL", "ok", "Base accessible", (time.perf_counter() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001 — on veut afficher n'importe quelle panne, pas la relancer
        return _ok("PostgreSQL", "erreur", str(exc)[:200])


async def _ollama() -> dict:
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
        if r.status_code != 200:
            return _ok("Ollama (modèle local)", "erreur", f"HTTP {r.status_code}")
        modeles = [m.get("name", "") for m in r.json().get("models", [])]
        attendus = [settings.ollama_model, settings.embed_model]
        manquants = [m for m in attendus if not any(str(x).startswith(m.split(":")[0]) for x in modeles)]
        if manquants:
            return _ok("Ollama (modèle local)", "attention", f"Modèle(s) absent(s) : {', '.join(manquants)}")
        return _ok("Ollama (modèle local)", "ok", f"{len(modeles)} modèle(s)", (time.perf_counter() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001
        return _ok("Ollama (modèle local)", "erreur", f"Injoignable sur {settings.ollama_url} ({type(exc).__name__})")


async def _pvgis() -> dict:
    """Service européen utilisé par le simulateur solaire. Requête minimale sur un point connu."""
    t0 = time.perf_counter()
    url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
    params = {"lat": 45.75, "lon": 4.85, "peakpower": 1, "loss": 14, "outputformat": "json"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, params=params)
        etat = "ok" if r.status_code == 200 else "erreur"
        return _ok("PVGIS (production solaire)", etat, f"HTTP {r.status_code}", (time.perf_counter() - t0) * 1000)
    except Exception as exc:  # noqa: BLE001
        return _ok("PVGIS (production solaire)", "erreur", f"Injoignable ({type(exc).__name__})")


def _anthropic() -> dict:
    """Pas d'appel réseau : un test consommerait des crédits pour rien. On rapporte la config."""
    if not settings.llm_api_key:
        return _ok("Claude (API)", "inactif", "Aucune clé configurée — Helios reste en mode local")
    return _ok("Claude (API)", "ok", f"Clé configurée · modèle {settings.llm_api_model}")


def _enedis() -> dict:
    if not settings.enedis_client_id:
        return _ok("Enedis DataConnect", "inactif", "Non raccordé — courbe de charge simulée")
    return _ok("Enedis DataConnect", "ok", "Identifiants configurés")


def _sobry() -> dict:
    if not settings.sobry_spot_api_url:
        return _ok("SOBRY (prix spot)", "inactif", "API non configurée — courbe de démonstration")
    return _ok("SOBRY (prix spot)", "ok", settings.sobry_spot_api_url)


async def _recherche_kb(db: AsyncSession) -> dict:
    """La recherche dans la base de connaissances est-elle EXACTE ?

    Pourquoi cette sonde existe : le 29/09/2026, un index `ivfflat` pose en migration 0002
    faisait rater la bonne fiche a presque toutes les questions. Un index approximatif ne
    visite qu'une fraction des vecteurs ; avec quelques centaines de fiches reparties en
    cent paquets, il n'en voyait que trois ou quatre par recherche. La migration 0020 l'a
    retire.

    Cette panne-la ne se voit pas : Helios continue de repondre, avec la mauvaise fiche.
    D'ou une sonde plutot qu'un test — c'est l'etat de la base qui compte, pas le code.
    """
    try:
        nb = await db.scalar(text("SELECT count(*) FROM kb_chunks"))
        index = await db.scalar(text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE tablename = 'kb_chunks' AND indexdef ILIKE '%ivfflat%'"
        ))
    except Exception as exc:  # noqa: BLE001
        return _ok("Recherche (base de connaissances)", "erreur", str(exc)[:200])
    if index:
        return _ok(
            "Recherche (base de connaissances)", "attention",
            f"Index approximatif ivfflat actif sur {nb} fiches : la bonne fiche peut être "
            "manquée sans que rien ne le signale. Voir la migration 0020.",
        )
    return _ok("Recherche (base de connaissances)", "ok", f"Exacte sur {nb} fiches")


async def etat_services(db: AsyncSession) -> dict:
    """Les sondes réseau tournent en parallèle : l'écran reste rapide même si l'une traîne."""
    postgres, ollama, pvgis = await asyncio.gather(_postgres(db), _ollama(), _pvgis())
    kb = await _recherche_kb(db)
    services = [postgres, kb, ollama, _anthropic(), pvgis, _enedis(), _sobry()]
    return {
        "services": services,
        "en_erreur": sum(1 for s in services if s["etat"] == "erreur"),
    }
