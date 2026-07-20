"""RAG au runtime — doc 07 §4 : recherche, seuil de pertinence, prompt avec constitution."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.house import House
from app.models.kb import KbChunk, KbDocument
from app.services.completeness import _is_filled, compute_score, niveau_for_score

# Version de constitution pilotée par la config (settings.constitution_version) — synchro avec le doc 03.
_CONSTITUTION_PATH = Path(__file__).resolve().parents[3] / "prompts" / f"constitution-{settings.constitution_version}.md"
_constitution_text = _CONSTITUTION_PATH.read_text(encoding="utf-8") if _CONSTITUTION_PATH.exists() else ""


async def search_chunks(db: AsyncSession, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    distance = KbChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(KbChunk, KbDocument, distance.label("distance"))
        .join(KbDocument, KbChunk.document_id == KbDocument.id)
        .where(KbDocument.statut != "obsolete")
        .order_by(distance)
        .limit(top_k or settings.rag_top_k)
    )
    rows = (await db.execute(stmt)).all()
    return [{"chunk": chunk, "document": document, "score": 1 - dist} for chunk, document, dist in rows]


def best_score(results: list[dict]) -> float:
    return max((r["score"] for r in results), default=0.0)


# Sources dont les chunks sont des fiches Q/R servables telles quelles (mêmes
# sources que la FAQ publique — cf. routers/faq.py).
_QR_SOURCES = ("faq_maison", "solutions", "pilotage", "eau")


def instant_answer(results: list[dict]) -> str | None:
    """Réponse instantanée sans LLM (doc 07 §5) : si la meilleure fiche Q/R matche
    quasi exactement la question, on sert sa réponse telle quelle — latence nulle,
    zéro risque d'hallucination. Sinon None → parcours LLM normal."""
    if not results:
        return None
    best = results[0]
    if best["score"] < settings.rag_instant_answer_threshold:
        return None
    if best["document"].source not in _QR_SOURCES:
        return None
    content = best["chunk"].content
    marker = "\nR:"
    idx = content.find(marker)
    if idx == -1:
        return None
    return content[idx + len(marker):].strip()


def build_citations(results: list[dict]) -> list[dict]:
    if not results or best_score(results) < settings.rag_score_threshold:
        return []
    return [
        {
            "titre": r["document"].titre,
            "cat": r["chunk"].chunk_metadata.get("cat"),
            "score": round(r["score"], 3),
        }
        for r in results
    ]


# Champs exclus du contexte envoyé au LLM externe (doc 10 sécurité : anonymiser la fiche,
# jamais nom/email, PDL exclu des prompts). `pdl` est une donnée personnelle sensible
# (identifiant de compteur) qui n'apporte rien au conseil : on ne l'envoie jamais au modèle.
_HOUSE_CONTEXT_EXCLUDE = {
    "id", "user_id", "completeness_score", "updated_at",
    "pdl",  # confidentialité (doc 10)
}


def build_house_context(house: House) -> dict:
    """Contexte fiche Maison pour le mode connecté (doc 03 §7) — uniquement les champs renseignés,
    hors données personnelles sensibles (PDL exclu, doc 10 sécurité).

    NB : ne contient pas encore le "dernier audit" mentionné au doc 03 §7 — le
    moteur de pré-audit n'existe pas avant le jalon 6. Point d'extension futur.
    """
    profil = {
        c.name: getattr(house, c.name)
        for c in house.__table__.columns
        if c.name not in _HOUSE_CONTEXT_EXCLUDE and _is_filled(getattr(house, c.name))
    }
    score = compute_score(house)
    return {"score": score, "niveau": niveau_for_score(score), "profil": profil}


def build_pro_context(profile) -> dict:
    """Contexte professionnel pour le chat — Helios détecte un client pro et adapte ses conseils."""
    return {
        "raison_sociale": profile.raison_sociale,
        "secteur": profile.secteur,
        "surface_m2": profile.surface_m2,
        "effectif": profile.effectif,
        "equipements": profile.equipements or [],
        "conso_annuelle_kwh": profile.conso_annuelle_kwh,
        "puissance_kva": profile.puissance_kva,
        "fournisseur_actuel": profile.fournisseur_actuel,
        "contrat_actuel": profile.contrat_actuel,
    }


def build_prompt(
    question: str,
    results: list[dict],
    house_context: dict | None = None,
    pro_context: dict | None = None,
) -> str:
    if not results or best_score(results) < settings.rag_score_threshold:
        sources_block = (
            "Aucune source fiable trouvée dans la base de connaissances pour cette question. "
            "Réponds prudemment, sans inventer de chiffre ni de règle."
        )
    else:
        sources_block = "\n\n".join(f"[Source {i + 1}] {r['chunk'].content}" for i, r in enumerate(results))

    if pro_context is not None:
        # Le contexte pro prime : Helios s'adresse à un professionnel et adapte questions/conseils.
        mode_block = (
            "MODE CONNECTÉ — CLIENT PROFESSIONNEL. Profil pro (JSON) :\n"
            f"{json.dumps(pro_context, ensure_ascii=False, default=str)}\n"
            "Adapte tes conseils au métier et aux équipements de ce professionnel (postes énergivores "
            "du secteur, pilotage, contrat pro négociable, potentiel de courtage). Reste franc et indépendant."
        )
        question_label = "Question du client professionnel"
    elif house_context is not None:
        mode_block = (
            "MODE CONNECTÉ — fiche foyer de ce visiteur (JSON, uniquement les champs renseignés) :\n"
            f"{json.dumps(house_context, ensure_ascii=False, default=str)}\n"
            "Adapte ta réponse à ce foyer précis. Si un champ décisif pour répondre manque, "
            "pose la question ou indique quel champ renseigner plutôt que de deviner (doc 03 §4)."
        )
        question_label = "Question de l'utilisateur connecté"
    else:
        mode_block = "MODE PUBLIC (visiteur) — pas de fiche foyer associée."
        question_label = "Question du visiteur"

    return (
        f"{_constitution_text}\n\n"
        "---\n"
        f"{mode_block}\n\n"
        "---\n"
        "SOURCES DISPONIBLES (ne cite que celles fournies ici, jamais d'autres) :\n"
        f"{sources_block}\n\n"
        "---\n"
        f"{question_label} : {question}\n"
        "Réponse d'Helios :"
    )
