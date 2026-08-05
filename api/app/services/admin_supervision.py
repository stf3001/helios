"""Supervision d'Helios et de sa base de connaissances — cœur du back-office.

Deux questions auxquelles ce module répond :
1. « Qu'est-ce qu'Helios a répondu, et est-ce qu'il l'a bien fait ? » (conversations)
2. « Que ne sait-il pas, et quel contenu ne sert à rien ? » (questions sans réponse, fiches
   jamais remontées) — c'est ce qui pilote l'écriture de nouvelles fiches.

Choix produit assumé : les conversations sont consultables avec l'identité du foyer
(email, prénom). Décision explicite du responsable de la plateforme.
"""

import uuid

from sqlalchemy import Float, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.models.kb import KbDocument
from app.models.user import User


async def liste_conversations(
    db: AsyncSession, limit: int = 50, offset: int = 0, mode: str | None = None
) -> dict:
    """Conversations les plus récentes, avec le nombre de messages et l'identité du foyer.

    `sans_reponse` : au moins un échange où aucune source pertinente n'a été trouvée —
    permet de repérer d'un coup d'œil les conversations à examiner.
    """
    filtres = []
    if mode in ("public", "connecte"):
        filtres.append(Conversation.mode == mode)

    total = await db.scalar(
        select(func.count()).select_from(Conversation).where(*filtres) if filtres
        else select(func.count()).select_from(Conversation)
    )

    stmt = (
        select(
            Conversation.id,
            Conversation.mode,
            Conversation.started_at,
            User.email,
            User.prenom,
            func.count(Message.id).label("nb_messages"),
            func.min(Message.rag_score).label("pire_score"),
            func.max(Message.created_at).label("dernier_message"),
        )
        .select_from(Conversation)
        .outerjoin(User, Conversation.user_id == User.id)
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id, Conversation.mode, Conversation.started_at, User.email, User.prenom)
        .order_by(desc(func.coalesce(func.max(Message.created_at), Conversation.started_at)))
        .limit(limit)
        .offset(offset)
    )
    if filtres:
        stmt = stmt.where(*filtres)

    lignes = (await db.execute(stmt)).all()
    return {
        "total": total or 0,
        "conversations": [
            {
                "id": str(r.id),
                "mode": r.mode,
                "started_at": r.started_at,
                "dernier_message": r.dernier_message,
                "email": r.email,
                "prenom": r.prenom,
                "nb_messages": r.nb_messages,
                "sans_reponse": r.pire_score is not None and r.pire_score < settings.rag_score_threshold,
            }
            for r in lignes
        ],
    }


async def detail_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> dict | None:
    """Échange complet : chaque message avec sa voie de réponse, ses citations et son coût."""
    conv = await db.get(Conversation, conversation_id)
    if conv is None:
        return None

    user = await db.get(User, conv.user_id) if conv.user_id else None
    messages = (
        await db.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
    ).all()

    return {
        "id": str(conv.id),
        "mode": conv.mode,
        "started_at": conv.started_at,
        "foyer": {"email": user.email, "prenom": user.prenom} if user else None,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "model_used": m.model_used,
                "rag_score": round(m.rag_score, 3) if m.rag_score is not None else None,
                "citations": m.citations,
                "tokens": m.tokens,
                "cout_eur": m.estimated_cost_eur,
                "constitution_version": m.constitution_version,
            }
            for m in messages
        ],
        "seuil_pertinence": settings.rag_score_threshold,
    }


async def questions_sans_reponse(db: AsyncSession, limit: int = 100) -> list[dict]:
    """Les questions pour lesquelles aucune source n'a atteint le seuil de pertinence.

    C'est la feuille de route de la base de connaissances : ces questions viennent des
    usages réels, pas d'une intuition. La question de l'utilisateur est le message qui
    précède immédiatement la réponse d'Helios dans la même conversation.
    """
    reponse = Message.__table__.alias("reponse")
    question = Message.__table__.alias("question")

    stmt = (
        select(
            reponse.c.id,
            reponse.c.created_at,
            reponse.c.rag_score,
            reponse.c.conversation_id,
            question.c.content.label("question"),
        )
        .select_from(reponse)
        .join(
            question,
            (question.c.conversation_id == reponse.c.conversation_id)
            & (question.c.role == "user")
            & (question.c.created_at <= reponse.c.created_at),
        )
        .where(
            reponse.c.role == "helios",
            reponse.c.rag_score.is_not(None),
            reponse.c.rag_score < settings.rag_score_threshold,
        )
        .distinct(reponse.c.id)
        # DISTINCT ON exige que la 1re clé de tri soit celle du DISTINCT : on prend la question
        # la plus proche (la plus récente antérieure à la réponse).
        .order_by(reponse.c.id, desc(question.c.created_at))
        .limit(limit)
    )
    lignes = (await db.execute(stmt)).all()
    lignes.sort(key=lambda r: r.created_at, reverse=True)
    return [
        {
            "question": r.question,
            "score": round(r.rag_score, 3),
            "created_at": r.created_at,
            "conversation_id": str(r.conversation_id),
        }
        for r in lignes
    ]


async def base_connaissances_detail(db: AsyncSession) -> dict:
    """Quelles fiches servent, lesquelles ne servent jamais.

    NB de vocabulaire : `messages.chunks_used` contient TOUTES les fiches remontées par la
    recherche (top-k), pas seulement celles finalement citées dans la réponse. On parle donc
    de fiches « remontées », ce qui reste le bon signal d'utilité.
    """
    remontees = (
        await db.execute(
            text(
                """
                WITH used AS (
                    SELECT (cid)::uuid AS chunk_id
                    FROM messages m
                    CROSS JOIN LATERAL jsonb_array_elements_text(m.chunks_used) AS cid
                    WHERE m.chunks_used IS NOT NULL
                )
                SELECT d.titre, d.source, COUNT(*) AS n
                FROM used u
                JOIN kb_chunks c ON c.id = u.chunk_id
                JOIN kb_documents d ON d.id = c.document_id
                GROUP BY d.id, d.titre, d.source
                ORDER BY n DESC
                LIMIT 15
                """
            )
        )
    ).all()

    jamais = (
        await db.execute(
            text(
                """
                WITH used AS (
                    SELECT DISTINCT (cid)::uuid AS chunk_id
                    FROM messages m
                    CROSS JOIN LATERAL jsonb_array_elements_text(m.chunks_used) AS cid
                    WHERE m.chunks_used IS NOT NULL
                )
                SELECT d.titre, d.source, d.date_maj
                FROM kb_documents d
                WHERE d.statut = 'actif'
                  AND NOT EXISTS (
                      SELECT 1 FROM kb_chunks c
                      JOIN used u ON u.chunk_id = c.id
                      WHERE c.document_id = d.id
                  )
                ORDER BY d.source, d.titre
                """
            )
        )
    ).all()

    par_source = dict(
        (row[0], row[1])
        for row in (
            await db.execute(
                select(KbDocument.source, func.count())
                .where(KbDocument.statut == "actif")
                .group_by(KbDocument.source)
                .order_by(desc(func.count()))
            )
        ).all()
    )

    obsoletes = (
        await db.scalars(
            select(KbDocument).where(KbDocument.statut == "obsolete").order_by(KbDocument.date_maj)
        )
    ).all()

    # Contexte de volume, indispensable pour ne pas surinterpréter « jamais remontée » :
    # chaque réponse ne mobilise que `rag_top_k` fiches. Tant que le nombre de réponses est
    # faible devant la taille du corpus, une fiche non remontée ne prouve rien.
    nb_reponses = await db.scalar(
        select(func.count()).select_from(Message).where(Message.chunks_used.is_not(None))
    ) or 0
    total_fiches = sum(par_source.values())

    return {
        "par_source": par_source,
        "plus_remontees": [{"titre": r.titre, "source": r.source, "n": r.n} for r in remontees],
        "jamais_remontees": [
            {"titre": r.titre, "source": r.source, "date_maj": r.date_maj} for r in jamais
        ],
        "obsoletes": [{"titre": d.titre, "source": d.source, "date_maj": d.date_maj} for d in obsoletes],
        "volume": {
            "reponses_avec_sources": nb_reponses,
            "tirages_max": nb_reponses * settings.rag_top_k,
            "total_fiches": total_fiches,
            # En dessous de ~3 tirages par fiche, l'absence n'est pas un signal exploitable.
            "echantillon_suffisant": nb_reponses * settings.rag_top_k >= 3 * total_fiches,
        },
    }


async def cout_par_utilisateur(db: AsyncSession, limit: int = 20) -> list[dict]:
    """Consommation d'API par foyer — repère un usage anormal avant qu'il ne pèse sur le budget."""
    stmt = (
        select(
            User.email,
            func.count(Message.id).label("appels"),
            func.coalesce(func.sum(Message.estimated_cost_eur.cast(Float)), 0.0).label("cout"),
        )
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .join(User, Conversation.user_id == User.id)
        .where(Message.model_used == "api")
        .group_by(User.email)
        .order_by(desc("cout"))
        .limit(limit)
    )
    return [
        {"email": r.email, "appels": r.appels, "cout_eur": round(r.cout or 0, 4)}
        for r in (await db.execute(stmt)).all()
    ]
