import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.ratelimit import limiter
from app.models.conversation import Conversation, Message
from app.models.house import House
from app.models.pro import ProProfile
from app.models.user import User
from app.schemas.chat import ChatIn
from app.services import ollama_client, rag, router_llm

router = APIRouter(prefix="/chat", tags=["chat"])


def _owner_ok(conversation: Conversation, user: User | None) -> bool:
    return conversation.user_id is None or (user is not None and conversation.user_id == user.id)


@router.post("/messages")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    payload: ChatIn,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat Helios — public (mode visiteur) ou connecté selon le token fourni (doc 07 §4-5)."""
    mode = "connecte" if user else "public"

    if payload.conversation_id:
        conversation = await db.get(Conversation, payload.conversation_id)
        if conversation is None or not _owner_ok(conversation, user):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    else:
        conversation = Conversation(mode=mode, user_id=user.id if user else None)
        db.add(conversation)
        await db.flush()

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.content))
    await db.commit()

    house_context = None
    pro_context = None
    niveau = None
    if user:
        pro = await db.scalar(select(ProProfile).where(ProProfile.user_id == user.id))
        if pro is not None:
            pro_context = rag.build_pro_context(pro)  # Helios détecte un client pro et adapte
        house = await db.scalar(select(House).where(House.user_id == user.id))
        if house is not None:
            house_context = rag.build_house_context(house)
            niveau = house_context["niveau"]

    query_embedding = await ollama_client.embed(payload.content)
    results = await rag.search_chunks(db, query_embedding)
    citations = rag.build_citations(results)
    chunks_used = [str(r["chunk"].id) for r in results]
    conversation_id = conversation.id

    # Réponse instantanée (doc 07 §5) : fiche Q/R quasi identique → on la sert sans LLM.
    # `force_llm` (bouton « développer » du widget) désactive le court-circuit.
    if not payload.force_llm:
        instant = rag.instant_answer(results)
        if instant is not None:
            instant_citations = citations[:1]

            async def stream_instant():
                yield json.dumps(
                    {
                        "type": "conversation",
                        "conversation_id": str(conversation_id),
                        "mode": mode,
                        "simplified": False,
                        "instant": True,
                    }
                ) + "\n"
                yield json.dumps({"type": "token", "text": instant}) + "\n"
                yield json.dumps({"type": "citations", "citations": instant_citations}) + "\n"

                async with async_session() as db2:
                    db2.add(
                        Message(
                            conversation_id=conversation_id,
                            role="helios",
                            content=instant,
                            model_used="kb",
                            citations=instant_citations,
                            chunks_used=chunks_used[:1],
                            constitution_version=settings.constitution_version,
                        )
                    )
                    await db2.commit()

            return StreamingResponse(stream_instant(), media_type="application/x-ndjson")

    prompt = rag.build_prompt(payload.content, results, house_context, pro_context)

    route, simplified, token_stream = await router_llm.generate_route(
        db,
        mode=mode,
        niveau=niveau,
        message=payload.content,
        user_id=user.id if user else None,
        prompt=prompt,
    )

    async def stream():
        yield json.dumps(
            {"type": "conversation", "conversation_id": str(conversation_id), "mode": mode, "simplified": simplified}
        ) + "\n"

        full_response = ""
        async for token in token_stream:
            full_response += token
            yield json.dumps({"type": "token", "text": token}) + "\n"

        yield json.dumps({"type": "citations", "citations": citations}) + "\n"

        # Nouvelle session : la dépendance `db` de la requête est fermée dès que
        # la StreamingResponse est retournée, avant la fin du streaming.
        tokens = len(full_response) // 4 or None  # approximation grossière (doc : à calibrer)
        cost = router_llm.estimate_cost_eur(tokens) if route == "api" else None
        async with async_session() as db2:
            db2.add(
                Message(
                    conversation_id=conversation_id,
                    role="helios",
                    content=full_response,
                    model_used=route,
                    tokens=tokens,
                    citations=citations,
                    chunks_used=chunks_used,
                    constitution_version=settings.constitution_version,
                    estimated_cost_eur=cost,
                )
            )
            await db2.commit()

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.get("/conversations")
async def list_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Historique des conversations de l'utilisateur connecté (doc 10 J4)."""
    rows = await db.scalars(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.started_at.desc())
    )
    return [{"id": c.id, "mode": c.mode, "started_at": c.started_at} for c in rows]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")

    rows = await db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content, "citations": m.citations, "created_at": m.created_at}
        for m in rows
    ]
