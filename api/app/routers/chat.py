import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session, get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatIn
from app.services import ollama_client, rag

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages")
async def send_message(payload: ChatIn, db: AsyncSession = Depends(get_db)):
    """Chat public (mode visiteur, doc 07 §4) : RAG + génération locale streamée + citations."""
    if payload.conversation_id:
        conversation = await db.get(Conversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    else:
        conversation = Conversation(mode="public")
        db.add(conversation)
        await db.flush()

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.content))
    await db.commit()

    query_embedding = await ollama_client.embed(payload.content)
    results = await rag.search_chunks(db, query_embedding)
    prompt = rag.build_prompt(payload.content, results)
    citations = rag.build_citations(results)
    conversation_id = conversation.id

    async def stream():
        yield json.dumps({"type": "conversation", "conversation_id": str(conversation_id)}) + "\n"

        full_response = ""
        async for token in ollama_client.generate_stream(prompt):
            full_response += token
            yield json.dumps({"type": "token", "text": token}) + "\n"

        yield json.dumps({"type": "citations", "citations": citations}) + "\n"

        # Nouvelle session : la dépendance `db` de la requête est fermée dès que
        # la StreamingResponse est retournée, avant la fin du streaming.
        async with async_session() as db2:
            db2.add(
                Message(
                    conversation_id=conversation_id,
                    role="helios",
                    content=full_response,
                    model_used="local",
                )
            )
            await db2.commit()

    return StreamingResponse(stream(), media_type="application/x-ndjson")
