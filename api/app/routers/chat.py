import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.ratelimit import limiter
from app.models.audit import Audit
from app.models.conversation import Conversation, Message
from app.models.energy import EnergyStudy
from app.models.house import House
from app.models.moderation import MOTIFS, MessageReport
from app.models.pro import ProProfile
from app.models.autoconso import AutoconsoStudy
from app.models.simulateur import SimulateurStudy
from app.models.solar import SolarStudy
from app.models.user import User
from app.models.water import WaterStudy
from app.schemas.chat import ChatIn
from app.services import civilites, ollama_client, rag, router_llm

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
    autoconso_context = None
    simulation_context = None
    solar_context = None
    audit_context = None
    energy_context = None
    water_context = None
    niveau = None
    if user:
        pro = await db.scalar(select(ProProfile).where(ProProfile.user_id == user.id))
        if pro is not None:
            pro_context = rag.build_pro_context(pro)  # Helios détecte un client pro et adapte
        house = await db.scalar(select(House).where(House.user_id == user.id))
        if house is not None:
            house_context = rag.build_house_context(house)
            niveau = house_context["niveau"]

            autoconso_study = await db.scalar(
                select(AutoconsoStudy).where(AutoconsoStudy.house_id == house.id).order_by(AutoconsoStudy.created_at.desc())
            )
            if autoconso_study is not None:
                autoconso_context = rag.build_autoconso_context(autoconso_study)

            etude_simulateur = await db.scalar(
                select(SimulateurStudy)
                .where(SimulateurStudy.house_id == house.id)
                .order_by(SimulateurStudy.created_at.desc())
            )
            if etude_simulateur is not None:
                simulation_context = rag.build_simulation_context(etude_simulateur)

            solar_study = await db.scalar(
                select(SolarStudy).where(SolarStudy.house_id == house.id).order_by(SolarStudy.created_at.desc())
            )
            if solar_study is not None:
                solar_context = rag.build_solar_context(solar_study)

            audit = await db.scalar(
                select(Audit).where(Audit.house_id == house.id).order_by(Audit.created_at.desc())
            )
            if audit is not None:
                audit_context = rag.build_audit_context(audit)

            energy_study = await db.scalar(
                select(EnergyStudy).where(EnergyStudy.house_id == house.id).order_by(EnergyStudy.created_at.desc())
            )
            if energy_study is not None:
                energy_context = rag.build_energy_context(energy_study)

            water_study = await db.scalar(
                select(WaterStudy).where(WaterStudy.house_id == house.id).order_by(WaterStudy.created_at.desc())
            )
            if water_study is not None:
                water_context = rag.build_water_context(water_study)

    # Civilité seule (« bonjour », « allo ? », « merci ») : réponse écrite, servie en
    # quelques millisecondes. On sort AVANT le calcul d'embedding — il n'y a rien à
    # chercher dans la base de connaissances, et rien à faire rédiger : la chaîne complète
    # coûtait jusqu'à une minute pour un « allo ?? ». Voir `civilites.py` pour le filet,
    # volontairement étroit.
    #
    # `force_llm` n'est pas consulté : le bouton « développer » ne s'affiche pas sur ces
    # réponses, et il n'y a rien à développer sur un « merci ».
    civilite = civilites.repondre(payload.content)
    if civilite is not None:
        conversation_id = conversation.id

        async def stream_civilite():
            yield json.dumps(
                {
                    "type": "conversation",
                    "conversation_id": str(conversation_id),
                    "mode": mode,
                    "simplified": False,
                    # Ni « instant » (ce n'est pas une fiche de la base) ni citation : c'est
                    # une politesse. Le drapeau sert à l'écran, qui fait alors saluer Helios
                    # au lieu de lui faire hausser les épaules faute de source citée.
                    "civilite": True,
                }
            ) + "\n"
            yield json.dumps({"type": "token", "text": civilite}) + "\n"

            async with async_session() as db2:
                msg = Message(
                    conversation_id=conversation_id,
                    role="helios",
                    content=civilite,
                    # `rag_score` reste nul : une politesse n'est pas un trou de la base de
                    # connaissances, et elle ne doit pas gonfler les « questions sans réponse ».
                    model_used="civilite",
                    constitution_version=settings.constitution_version,
                )
                db2.add(msg)
                await db2.commit()
                yield json.dumps({"type": "message_id", "message_id": str(msg.id)}) + "\n"

        return StreamingResponse(stream_civilite(), media_type="application/x-ndjson")

    query_embedding = await ollama_client.embed(payload.content)
    results = await rag.search_chunks(db, query_embedding)
    citations = rag.build_citations(results)
    # Meilleur score de similarité : tracé sur la réponse pour le back-office. Sous le seuil
    # de pertinence, la question révèle un trou de la base de connaissances (module admin).
    rag_score = rag.best_score(results)
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
                    msg = Message(
                        conversation_id=conversation_id,
                        role="helios",
                        content=instant,
                        model_used="kb",
                        citations=instant_citations,
                        chunks_used=chunks_used[:1],
                        constitution_version=settings.constitution_version,
                        rag_score=rag_score,
                    )
                    db2.add(msg)
                    await db2.commit()
                    # Envoyé en dernier : permet au widget de proposer « signaler cette réponse ».
                    yield json.dumps({"type": "message_id", "message_id": str(msg.id)}) + "\n"

            return StreamingResponse(stream_instant(), media_type="application/x-ndjson")

    user_content = rag.build_user_content(
        payload.content,
        results,
        house_context,
        pro_context,
        autoconso_context,
        solar_context,
        audit_context,
        energy_context,
        water_context,
        simulation_context=simulation_context,
    )

    route, simplified, token_stream = await router_llm.generate_route(
        db,
        mode=mode,
        niveau=niveau,
        message=payload.content,
        user_id=user.id if user else None,
        user_content=user_content,
        has_recent_audit=audit_context is not None,
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
            msg = Message(
                conversation_id=conversation_id,
                role="helios",
                content=full_response,
                model_used=route,
                tokens=tokens,
                citations=citations,
                chunks_used=chunks_used,
                constitution_version=settings.constitution_version,
                estimated_cost_eur=cost,
                rag_score=rag_score,
            )
            db2.add(msg)
            await db2.commit()
            # Envoyé en dernier : permet au widget de proposer « signaler cette réponse ».
            yield json.dumps({"type": "message_id", "message_id": str(msg.id)}) + "\n"

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


class SignalementIn(BaseModel):
    """Signalement d'une réponse d'Helios par le foyer (ou un visiteur)."""

    message_id: uuid.UUID
    motif: str
    commentaire: str | None = None


@router.post("/signaler", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def signaler_reponse(
    request: Request,
    payload: SignalementIn,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Signale une réponse fausse, hors sujet ou gênante — alimente la revue admin.

    Ouvert aux visiteurs anonymes (le chat public l'est aussi). On vérifie seulement que le
    message existe et qu'il vient bien d'Helios : signaler sa propre question n'aurait pas de sens.
    """
    if payload.motif not in MOTIFS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Motif invalide (attendu : {', '.join(MOTIFS)})")

    message = await db.get(Message, payload.message_id)
    if message is None or message.role != "helios":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message introuvable")

    db.add(
        MessageReport(
            message_id=message.id,
            user_id=user.id if user else None,
            motif=payload.motif,
            commentaire=(payload.commentaire or "").strip()[:2000] or None,
        )
    )
    await db.commit()
    return {"enregistre": True, "message": "Merci — ce signalement est examiné par l'équipe."}
