"""Agents automatisés — doc 10 J10 : crawler d'ingestion + veille, alimentant le RAG.

Unifie l'ingestion : au lieu du script manuel, des *sources* déclarées sont parcourues,
parsées, embarquées (embeddings) et upsertées dans kb_documents/kb_chunks. Chaque exécution
est journalisée dans agents_log. La veille repère les contenus périmés (aides/prix) à rafraîchir.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.models.kb import KbChunk, KbDocument
from app.services.ollama_client import embed

_REPO_ROOT = Path(__file__).resolve().parents[3].parent  # dossier HELIOS (parent de helios/)


@dataclass
class SourceSpec:
    name: str          # identifiant stocké dans kb_documents.source
    kind: str          # "faq_markdown" | "web"
    location: str      # chemin de fichier (relatif à HELIOS/) ou URL
    cat: str | None = None
    verif: str | None = None


# Registre des sources. La FAQ locale est la source canonique (fiable, hors réseau).
# Les sources "web" (aides/prix) sont optionnelles : un échec réseau est journalisé, non bloquant.
SOURCES: list[SourceSpec] = [
    SourceSpec(name="faq_maison", kind="faq_markdown", location="05-FAQ-V1.md"),
    SourceSpec(name="solutions", kind="faq_markdown", location="helios/kb/solutions.md"),
    SourceSpec(name="pilotage", kind="faq_markdown", location="helios/kb/pilotage.md"),
    SourceSpec(name="eau", kind="faq_markdown", location="helios/kb/eau.md"),
]

_FAQ_RE = re.compile(
    r"^### Q:\s*(?P<question>.+?)\s*\n`(?P<meta>[^`]+)`\s*\n"
    r"R:\s*(?P<answer>.+?)(?=\n### Q:|\n## |\n---|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _parse_meta(meta: str) -> dict:
    out: dict = {}
    for part in meta.split("|"):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        key, value = key.strip(), value.strip()
        out[key] = [t.strip() for t in value.split(",") if t.strip()] if key == "tags" else value
    return out


def parse_faq_markdown(text: str) -> list[dict]:
    """Parse un fichier FAQ (### Q: / `meta` / R:) en entrées {titre, content, metadata}."""
    entries = []
    for m in _FAQ_RE.finditer(text):
        question = m.group("question").strip()
        answer = m.group("answer").strip()
        meta = _parse_meta(m.group("meta"))
        entries.append({
            "titre": question,
            "content": f"Q: {question}\nR: {answer}",
            "metadata": {"cat": meta.get("cat"), "tags": meta.get("tags", []),
                         "verif": meta.get("verif"), "niveau_confiance": "officiel"},
        })
    return entries


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, size: int = 800) -> list[str]:
    words, chunks, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size:
            chunks.append(cur.strip())
            cur = ""
        cur += " " + w
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


async def _fetch_source_entries(source: SourceSpec) -> list[dict]:
    if source.kind == "faq_markdown":
        text = (_REPO_ROOT / source.location).read_text(encoding="utf-8")
        return parse_faq_markdown(text)
    if source.kind == "web":
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            res = await client.get(source.location)
            res.raise_for_status()
        text = _html_to_text(res.text)
        return [
            {"titre": f"{source.name} #{i + 1}", "content": chunk,
             "metadata": {"cat": source.cat, "tags": [], "verif": source.verif, "niveau_confiance": "veille"}}
            for i, chunk in enumerate(_chunk_text(text))
        ]
    raise ValueError(f"Type de source inconnu : {source.kind}")


async def _log(db: AsyncSession, agent: str, action: str, detail: str) -> None:
    db.add(AgentLog(agent=agent, action=action, detail=detail))


async def crawl_source(db: AsyncSession, source: SourceSpec) -> dict:
    """Ingestion/rafraîchissement d'une source dans le RAG. Upsert par (source, titre)."""
    try:
        entries = await _fetch_source_entries(source)
    except Exception as exc:  # réseau, parsing… — journalisé, non bloquant
        await _log(db, "crawler", "error", f"{source.name}: {exc}")
        await db.commit()
        return {"source": source.name, "error": str(exc)}

    added = updated = 0
    today = date.today()
    for entry in entries:
        doc = await db.scalar(
            select(KbDocument).where(KbDocument.source == source.name, KbDocument.titre == entry["titre"])
        )
        if doc is None:
            doc = KbDocument(source=source.name, titre=entry["titre"], date_maj=today, statut="actif")
            db.add(doc)
            await db.flush()
            added += 1
        else:
            doc.date_maj = today
            updated += 1

        embedding = await embed(entry["content"])
        chunk = await db.scalar(select(KbChunk).where(KbChunk.document_id == doc.id))
        if chunk is None:
            db.add(KbChunk(document_id=doc.id, content=entry["content"], embedding=embedding,
                           chunk_metadata=entry["metadata"]))
        else:
            chunk.content = entry["content"]
            chunk.embedding = embedding
            chunk.chunk_metadata = entry["metadata"]

    await _log(db, "crawler", "ingest_source",
               f"{source.name}: {added} ajoutés, {updated} mis à jour ({len(entries)} entrées)")
    await db.commit()
    return {"source": source.name, "added": added, "updated": updated, "total": len(entries)}


async def run_crawler(db: AsyncSession) -> list[dict]:
    """Parcourt toutes les sources déclarées."""
    return [await crawl_source(db, s) for s in SOURCES]


async def run_veille(db: AsyncSession, max_age_days: int = 180) -> dict:
    """Repère les documents périmés (date_maj trop ancienne) à faire vérifier/rafraîchir."""
    seuil = date.today() - timedelta(days=max_age_days)
    stale = list(await db.scalars(
        select(KbDocument).where(KbDocument.date_maj < seuil, KbDocument.statut == "actif")
    ))
    for doc in stale:
        await _log(db, "veille", "stale_flag",
                   f"À vérifier : '{doc.titre}' (source {doc.source}, maj {doc.date_maj})")
    await _log(db, "veille", "run", f"{len(stale)} document(s) périmé(s) sur seuil {max_age_days} j")
    await db.commit()
    return {"stale": len(stale), "seuil_jours": max_age_days,
            "titres": [d.titre for d in stale[:20]]}
