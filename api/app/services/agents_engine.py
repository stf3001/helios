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
    # Source historique (109 fiches d'origine). Déplacée depuis HELIOS/05-FAQ-V1.md vers le
    # dépôt le 27/07/2026 : elle vit désormais avec les autres fiches, donc versionnée en git.
    SourceSpec(name="faq_maison", kind="faq_markdown", location="helios/kb/faq_maison.md"),
    SourceSpec(name="solutions", kind="faq_markdown", location="helios/kb/solutions.md"),
    SourceSpec(name="pilotage", kind="faq_markdown", location="helios/kb/pilotage.md"),
    SourceSpec(name="eau", kind="faq_markdown", location="helios/kb/eau.md"),
    SourceSpec(name="autoconso", kind="faq_markdown", location="helios/kb/autoconso.md"),
    SourceSpec(name="complements", kind="faq_markdown", location="helios/kb/complements.md"),
    SourceSpec(name="cas_pratiques", kind="faq_markdown", location="helios/kb/cas_pratiques.md"),
    SourceSpec(name="baremes_aides", kind="faq_markdown", location="helios/kb/baremes_aides.md"),
    SourceSpec(name="confort_ete", kind="faq_markdown", location="helios/kb/confort_ete.md"),
    SourceSpec(name="reglementation", kind="faq_markdown", location="helios/kb/reglementation.md"),
    SourceSpec(name="voss", kind="faq_markdown", location="helios/kb/voss.md"),
    SourceSpec(name="vigilance", kind="faq_markdown", location="helios/kb/vigilance.md"),
    # Sources de terrain (109 fiches, ajoutees le 28/09/2026). Tirees de syntheses clients
    # anonymisees : elles apportent ce que la FAQ d'origine ignorait, notamment les contrats
    # d'obligation d'achat (resiliation, indemnite) et le raisonnement sur l'existant.
    SourceSpec(name="terrain", kind="faq_markdown", location="helios/kb/terrain.md"),
    SourceSpec(name="pac_air_eau", kind="faq_markdown", location="helios/kb/pac_air_eau.md"),
    SourceSpec(name="pac_air_air", kind="faq_markdown", location="helios/kb/pac_air_air.md"),
    SourceSpec(name="ecs_solaire", kind="faq_markdown", location="helios/kb/ecs_solaire.md"),
    SourceSpec(name="stockage_contrats", kind="faq_markdown", location="helios/kb/stockage_contrats.md"),
    SourceSpec(name="autonomie_hors_reseau", kind="faq_markdown", location="helios/kb/autonomie_hors_reseau.md"),
    SourceSpec(name="dimensionnement_pv", kind="faq_markdown", location="helios/kb/dimensionnement_pv.md"),
    SourceSpec(name="supports_securite", kind="faq_markdown", location="helios/kb/supports_securite.md"),
    SourceSpec(name="urbanisme_assurance", kind="faq_markdown", location="helios/kb/urbanisme_assurance.md"),
    SourceSpec(name="financement_projet", kind="faq_markdown", location="helios/kb/financement_projet.md"),
    SourceSpec(name="cas_terrain", kind="faq_markdown", location="helios/kb/cas_terrain.md"),
    # Fin de contrat de rachat et ajout de puissance (28/09/2026) : deux situations que la
    # base ignorait, alors qu'elles representent une bonne part des appels recus.
    SourceSpec(name="fin_contrat_rachat", kind="faq_markdown", location="helios/kb/fin_contrat_rachat.md"),
    # Parcours (28/09/2026) : l'ordre des decisions, verse en fiches quand la section Guides
    # a ete supprimee. Chez Helios on interroge le robot, on ne parcourt pas des pages.
    SourceSpec(name="parcours", kind="faq_markdown", location="helios/kb/parcours.md"),
    # Eolien domestique (29/09/2026), en meme temps que la page « Le vent » et que
    # l'eolienne du simulateur. Chiffres techniques du constructeur, regles d'urbanisme
    # marquees comme telles.
    SourceSpec(name="eolien", kind="faq_markdown", location="helios/kb/eolien.md"),
    # Le jardin nourricier (29/09/2026), en meme temps que la page « La terre » et que le
    # potager du simulateur. Les ordres de grandeur (kg par personne, kg/m2, heures
    # d'entretien) sont ceux de services/jardin.py : les deux doivent rester d'accord,
    # sinon le chat contredira le calculateur sur la meme page.
    SourceSpec(name="potager", kind="faq_markdown", location="helios/kb/potager.md"),
    # L'achat d'energie (30/09/2026), en meme temps que la page du meme nom. Les options
    # du tarif reglemente, la reforme des heures creuses, le courtage et sa commission.
    # Les prix y sont DATES (grille du 01/08/2026) : une grille change, une explication
    # non — c'est pour cela que les fiches expliquent d'abord et chiffrent ensuite.
    SourceSpec(name="achat_energie", kind="faq_markdown", location="helios/kb/achat_energie.md"),
]

# Sources dont les fiches sont des Q/R servables telles quelles : page FAQ publique
# (routers/faq.py) et reponse instantanee sans LLM (services/rag.py). Les deux tenaient
# chacune sa propre copie de la liste, avec un commentaire demandant de les garder
# identiques — une source ajoutee etait donc oubliee d'un cote ou de l'autre. Elle se
# deduit maintenant de SOURCES : les sources "web" en sont exclues (texte decoupe a
# l'aveugle, pas des Q/R), ainsi que les sources listees ci-dessous.
# `cas_terrain` : ses intitules sont des situations (« Cas de terrain : ... »), pas des
# questions. Precieux pour le raisonnement du chat, hors sujet dans une liste de questions.
_HORS_FAQ_PUBLIQUE = ("cas_terrain",)

SOURCES_QR: tuple[str, ...] = tuple(
    s.name for s in SOURCES if s.kind == "faq_markdown" and s.name not in _HORS_FAQ_PUBLIQUE
)

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


async def _elaguer(db: AsyncSession, source: SourceSpec, titres_du_fichier: set[str]) -> int:
    """Retire de la base les fiches de cette source qui ne sont plus dans son fichier.

    Sans ça le crawler ne sait qu'ajouter : une fiche supprimée du markdown restait en base
    pour toujours. Elle continuait d'être listée sur /faq alors que le pré-rendu, qui lit le
    markdown, ne lui générait plus de page — le lien « ouvrir cette fiche » tombait en 404 —
    et le chat pouvait encore la servir. Constaté le 29/09/2026 sur une fiche d'éolien.

    GARDE-FOU : on n'élague jamais à partir d'un fichier qui n'a produit aucune fiche. Une
    erreur de lecture ou une expression de parsing cassée effacerait sinon la source entière,
    silencieusement. Mieux vaut une fiche périmée de trop qu'une source disparue.

    Les chunks partent avant le document : la clé étrangère n'a pas de suppression en cascade.
    """
    if not titres_du_fichier:
        return 0

    perimes = list(await db.scalars(
        select(KbDocument).where(
            KbDocument.source == source.name,
            KbDocument.titre.notin_(titres_du_fichier),
        )
    ))
    for doc in perimes:
        for chunk in await db.scalars(select(KbChunk).where(KbChunk.document_id == doc.id)):
            await db.delete(chunk)
        await db.delete(doc)
        await _log(db, "crawler", "retrait", f"{source.name}: « {doc.titre} » n'est plus dans le fichier")
    return len(perimes)


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

    retires = await _elaguer(db, source, {e["titre"] for e in entries})

    await _log(db, "crawler", "ingest_source",
               f"{source.name}: {added} ajoutés, {updated} mis à jour, {retires} retirés "
               f"({len(entries)} entrées)")
    await db.commit()
    return {"source": source.name, "added": added, "updated": updated,
            "removed": retires, "total": len(entries)}


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
