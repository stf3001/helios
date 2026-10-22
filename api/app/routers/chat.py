import json
import logging
import re
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.ratelimit import limiter
from app.models.audit import Audit
from app.models.conversation import Conversation, Message
from app.models.energy import EnergyStudy
from app.models.equipement import Equipement
from app.models.house import House
from app.models.journal import JournalEntree
from app.models.risques import RisquesCommune
from app.models.moderation import MOTIFS, MessageReport
from app.models.partner import Partner
from app.models.piece import Emetteur, Piece
from app.models.pro import ProProfile
from app.models.autoconso import AutoconsoStudy
from app.models.simulateur import SimulateurStudy
from app.models.solar import SolarStudy
from app.models.travaux import Travaux
from app.models.user import User
from app.schemas.chat import ChatIn
from app.services import (civilites, ollama_client, rag, regions, risques_affichage, router_llm, vigilance,
                          vigilance_lecture)
from app.services.a_faire import derniers_faits, journal_fusionne
from app.services.carnet_contexte import carnet_contexte, parle_du_carnet
from app.services.entretien import echeances, table_courante
from app.services.garanties import age_ans, garanties_maison
from app.services.pieces import resume_pieces

logger = logging.getLogger("helios.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


def _vigilance_du_foyer(house: House, episodes) -> list | None:
    dep = regions.departement_du_code_postal(house.code_postal or "")
    return vigilance.pour_le_chat(vigilance.vigilances_du_foyer(dep, episodes, datetime.now(timezone.utc)))


# Les sujets du bloc `puissance` du pré-audit et du relevé de combustible (point 81).
_SUJET_PUISSANCE = re.compile(
    r"puissance|\bkw\b|kwh|radiateur|pompe [àa] chaleur|\bpac\b|fioul|granul|st[eè]re|relev[ée]",
    re.IGNORECASE,
)


async def _carnet_du_foyer(db: AsyncSession, house: House) -> dict | None:
    """Le résumé du carnet de maison pour le chat (lot 5), ou None.

    NE FAIT JAMAIS ÉCHOUER LE CHAT : une exception ici est journalisée et le contexte part
    sans carnet. Les moteurs des lots 1 à 4 sont appelés tels quels ; rien n'est recalculé ici.
    """
    try:
        aujourd_hui = date.today()
        equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
        travaux = list(await db.scalars(select(Travaux).where(Travaux.house_id == house.id)))
        entrees = list(await db.scalars(select(JournalEntree).where(JournalEntree.house_id == house.id)))
        pieces = list(await db.scalars(select(Piece).where(Piece.house_id == house.id)))
        emetteurs = list(await db.scalars(
            select(Emetteur).where(Emetteur.piece_id.in_([p.id for p in pieces])))) if pieces else []

        table = table_courante()
        echs = echeances(equipements, table["taches"], derniers_faits(entrees), aujourd_hui, maison=house)
        eqs = []
        for e in equipements:
            age, statut = age_ans(e, aujourd_hui)
            eqs.append({"id": e.id, "categorie": e.categorie, "type": e.type, "marque": e.marque,
                        "en_service": e.en_service, "contrat_entretien": e.contrat_entretien,
                        "age_ans": age, "age_statut": statut})
        carnet = carnet_contexte(
            eqs, echs, garanties_maison(equipements, travaux, aujourd_hui), journal_fusionne(entrees, travaux),
            resume_pieces(house, pieces, emetteurs) if pieces else None, aujourd_hui, travaux=travaux,
            # Phase 2 : les risques de la commune, relus du cache seulement — jamais d'appel réseau ici.
            risques=risques_affichage.pour_le_chat(
                await db.get(RisquesCommune, house.code_insee) if house.code_insee else None),
            vigilance=_vigilance_du_foyer(house, await vigilance_lecture.du_departement(
                db, regions.departement_du_code_postal(house.code_postal or ""))),
        )
        return carnet or None
    except Exception:
        logger.exception("Carnet de maison illisible pour le chat (maison %s) : contexte envoyé sans carnet", house.id)
        return None


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

    message_courant = Message(conversation_id=conversation.id, role="user", content=payload.content)
    db.add(message_courant)
    await db.commit()

    house_context = None
    #: Le departement du foyer, qui decide quels partenaires Helios a sous les yeux.
    departement = None
    pro_context = None
    autoconso_context = None
    simulation_context = None
    solar_context = None
    audit_context = None
    dernier_audit = None
    energy_context = None
    niveau = None
    if user:
        pro = await db.scalar(select(ProProfile).where(ProProfile.user_id == user.id))
        if pro is not None:
            pro_context = rag.build_pro_context(pro)  # Helios détecte un client pro et adapte
        house = await db.scalar(select(House).where(House.user_id == user.id))
        if house is not None:
            house_context = rag.build_house_context(house, carnet=await _carnet_du_foyer(db, house))
            niveau = house_context["niveau"]
            departement = regions.departement_du_code_postal(house.code_postal or "")

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
                dernier_audit = audit

            energy_study = await db.scalar(
                select(EnergyStudy).where(EnergyStudy.house_id == house.id).order_by(EnergyStudy.created_at.desc())
            )
            if energy_study is not None:
                energy_context = rag.build_energy_context(energy_study)

            # L'étude de potentiel hydrique n'est plus transmise (point 13) : elle repose sur une
            # table climatique provisoire d'Hydrolia (point 14). Les études restent en base.

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

    # ---- L'HISTORIQUE DE LA CONVERSATION ----
    # Il était écrit en base depuis le premier jour, et jamais relu : Helios recevait la
    # constitution, les fiches trouvées, la fiche du foyer et ses études — puis la question
    # SEULE. Dans une conversation, il ne se souvenait donc de rien. « Et pour une maison de
    # 1970 ? » n'avait aucun sens pour lui, « tu m'as dit 6 kWc » non plus.
    #
    # On relit les derniers tours APRÈS le court-circuit des civilités : un « merci » ne
    # mérite pas une requête de plus. Les réponses de politesse d'Helios sont écartées de
    # l'historique — elles n'apportent rien et prennent de la place.
    #
    # `model_used` est NULL sur les messages du visiteur, et en SQL `NULL != 'civilite'`
    # vaut NULL, donc faux : sans le `is_(None)`, le filtre écarterait TOUTES les questions.
    precedents = list(
        await db.scalars(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.id != message_courant.id,
                or_(Message.model_used.is_(None), Message.model_used != "civilite"),
            )
            .order_by(Message.created_at.desc())
            .limit(rag.HISTORIQUE_ECHANGES * 2)
        )
    )
    precedents.reverse()
    historique_context = rag.build_historique_context(precedents)

    # La question VECTORISÉE n'est pas toujours celle qu'on affiche : une relance courte se
    # voit recoller la question précédente, sans quoi la recherche n'a aucun sujet auquel se
    # raccrocher. Ce qui est enregistré, affiché et posé au modèle reste le texte du visiteur.
    recherche = rag.question_pour_recherche(payload.content, precedents)
    #: Vrai quand le sujet de la recherche a ete SUPPOSE d'apres le tour precedent, et non
    #: ecrit par le visiteur. Rend la reponse instantanee plus exigeante — voir plus bas.
    relance = recherche != payload.content
    query_embedding = await ollama_client.embed(recherche)
    results = await rag.search_chunks(db, query_embedding)
    citations = rag.build_citations(results)
    # Meilleur score de similarité : tracé sur la réponse pour le back-office. Sous le seuil
    # de pertinence, la question révèle un trou de la base de connaissances (module admin).
    rag_score = rag.best_score(results)
    chunks_used = [str(r["chunk"].id) for r in results]
    conversation_id = conversation.id

    # Question sur le carnet de CE foyer (« ma PAC », « mes travaux ») : elle va à Claude,
    # qui lit le carnet. Une fiche générale servie telle quelle répondrait à côté.
    question_carnet = bool(house_context and house_context.get("carnet") and parle_du_carnet(payload.content))
    # Point 81 : une question sur la puissance, les radiateurs ou le relevé d'un foyer dont le
    # pré-audit les calcule ne reçoit pas une fiche générale servie telle quelle (vérifié : « Mes
    # radiateurs suffiront-ils ? » recevait la méthode générale au lieu des verdicts du foyer).
    question_puissance = bool(audit_context and audit_context.get("puissance") and _SUJET_PUISSANCE.search(payload.content))

    # Série 9 : puissance, radiateurs, relevé ou puissance d'un devis → les phrases du pré-audit
    # du foyer, telles quelles, sans LLM (`model_used = "preaudit"`). Avant la fiche générale :
    # elles portent les chiffres de CETTE maison. `force_llm` (« développer ») passe outre.
    if not payload.force_llm and dernier_audit is not None:
        directe = rag.reponse_preaudit(dernier_audit.json_result, dernier_audit.created_at.isoformat(),
                                       payload.content)
        if directe is not None:

            async def stream_preaudit():
                yield json.dumps({"type": "conversation", "conversation_id": str(conversation_id), "mode": mode,
                                  "simplified": False, "instant": True}) + "\n"
                yield json.dumps({"type": "token", "text": directe}) + "\n"
                async with async_session() as db2:
                    msg = Message(conversation_id=conversation_id, role="helios", content=directe,
                                  model_used="preaudit", citations=[], chunks_used=[],
                                  constitution_version=settings.constitution_version, rag_score=rag_score)
                    db2.add(msg)
                    await db2.commit()
                    yield json.dumps({"type": "message_id", "message_id": str(msg.id)}) + "\n"

            return StreamingResponse(stream_preaudit(), media_type="application/x-ndjson")

    # Réponse instantanée (doc 07 §5) : fiche Q/R quasi identique → on la sert sans LLM.
    # `force_llm` (bouton « développer » du widget) désactive le court-circuit, comme une
    # question sur le carnet.
    if not payload.force_llm and not question_carnet and not question_puissance:
        instant = rag.instant_answer(results, relance=relance)
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

    # L'annuaire : les partenaires actifs qui couvrent le departement de CE foyer, ranges
    # par metier. On interroge a chaque message plutot que de mettre en cache — l'annuaire
    # bouge rarement, mais un partenaire suspendu ne doit jamais etre propose une fois de
    # trop. Sans departement connu (visiteur anonyme, ou code postal hors metropole), le
    # bloc dit a Helios de demander le code postal avant de citer qui que ce soit.
    par_metier: dict[str, list[str]] = {}
    if departement is not None:
        # Les partenaires de démonstration (point 60) ne sont jamais nommés par le chat.
        actifs = await db.scalars(select(Partner).where(Partner.statut == "actif", Partner.demo.is_(False)))
        for partenaire in actifs:
            if departement not in (partenaire.zones or []):
                continue
            for metier in partenaire.metiers or []:
                par_metier.setdefault(metier, []).append(partenaire.raison_sociale)
    partenaires_context = rag.build_partenaires_context(par_metier, departement)

    user_content = rag.build_user_content(
        payload.content,
        results,
        house_context,
        pro_context,
        autoconso_context,
        solar_context,
        audit_context,
        energy_context,
        simulation_context=simulation_context,
        partenaires_context=partenaires_context,
        historique_context=historique_context,
    )

    route, simplified, token_stream = await router_llm.generate_route(
        db,
        mode=mode,
        niveau=niveau,
        message=payload.content,
        user_id=user.id if user else None,
        user_content=user_content,
        has_recent_audit=audit_context is not None,
        question_carnet=question_carnet,
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
