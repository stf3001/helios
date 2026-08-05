"""Back-office HELIOS.

Deux voies d'accès acceptées (cf. `require_admin_access`) :
- `X-Admin-Token` : secret partagé, pour les scripts et l'outillage en ligne de commande ;
- JWT d'un compte `users.is_admin` : pour l'interface du back-office.

Le back-office est en LECTURE SEULE sur les données des foyers ; les seules écritures sont
les actions explicitement prévues sur les partenaires (activation / suspension).
"""
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session, get_db
from app.core.deps import require_admin_access
from app.core.security import hash_password
from app.models.agent_log import AgentLog
from app.routers import account
from app.models.conversation import Conversation, Message
from app.models.moderation import STATUTS, AdminAccessLog, MessageReport
from app.models.partner import Partner
from app.models.user import User
from app.services import admin_health, admin_stats, admin_supervision, agents_engine


async def _tracer(db: AsyncSession, admin: User | None, action: str, cible: str | None) -> None:
    """Journalise une consultation de données personnelles.

    Contrepartie de l'accès complet assumé : l'accès reste total, mais il est traçable.
    Un accès par secret partagé (script) est enregistré sous « secret_partagé ».
    """
    db.add(AdminAccessLog(admin_email=admin.email if admin else "secret_partagé", action=action, cible=cible))
    await db.commit()

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
async def admin_me(admin: User | None = Depends(require_admin_access)):
    """Vérifie l'accès et identifie la session (affiché dans l'en-tête du back-office).

    `admin` vaut None quand l'accès passe par le secret partagé (script sans compte).
    """
    if admin is None:
        return {"email": None, "prenom": None, "via": "secret_partage"}
    return {"id": admin.id, "email": admin.email, "prenom": admin.prenom, "via": "compte"}


@router.get("/dashboard")
async def dashboard(_: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)):
    """Tableau de bord : utilisateurs, activité d'Helios, coût IA, business, base de connaissances."""
    return await admin_stats.dashboard(db)


@router.get("/services")
async def services(_: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)):
    """État des services dont dépend la plateforme (diagnostic de panne)."""
    return await admin_health.etat_services(db)


@router.get("/agents-log")
async def agents_log(
    limit: int = 50, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Journal des agents (crawler + veille) — supervision de l'alimentation du RAG (doc 10)."""
    rows = await db.scalars(select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit))
    return [{"agent": r.agent, "action": r.action, "detail": r.detail, "created_at": r.created_at} for r in rows]


# --- Supervision d'Helios ---


@router.get("/conversations")
async def conversations(
    limit: int = 50,
    offset: int = 0,
    mode: str | None = None,
    _: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Conversations récentes. L'identité du foyer est affichée (choix produit assumé)."""
    return await admin_supervision.liste_conversations(db, limit=limit, offset=offset, mode=mode)


@router.get("/conversations/{conversation_id}")
async def conversation_detail(
    conversation_id: uuid.UUID,
    admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    detail = await admin_supervision.detail_conversation(db, conversation_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    # Lecture d'un échange nominatif → tracée (cf. `_tracer`).
    cible = (detail.get("foyer") or {}).get("email") or str(conversation_id)
    await _tracer(db, admin, "conversation_lue", cible)
    return detail


@router.get("/questions-sans-reponse")
async def questions_sans_reponse(
    limit: int = 100, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Questions dont aucune source n'a atteint le seuil de pertinence : quoi écrire ensuite."""
    return await admin_supervision.questions_sans_reponse(db, limit=limit)


@router.get("/cout-par-utilisateur")
async def cout_par_utilisateur(
    _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    return await admin_supervision.cout_par_utilisateur(db)


# --- Base de connaissances ---


@router.get("/kb")
async def kb_detail(_: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)):
    """Quelles fiches servent réellement, lesquelles ne remontent jamais."""
    return await admin_supervision.base_connaissances_detail(db)


async def _lancer_agent(agent: str) -> None:
    """Exécuté hors requête HTTP : le crawler prend plusieurs minutes (embeddings en local).
    Sa propre session est nécessaire, celle de la requête étant fermée entre-temps.
    La progression est journalisée dans `agents_log`, consultable dans l'écran Agents."""
    async with async_session() as db:
        try:
            if agent == "crawl":
                await agents_engine.run_crawler(db)
            else:
                await agents_engine.run_veille(db)
        except Exception as exc:  # noqa: BLE001 — l'échec doit être visible dans le journal
            db.add(AgentLog(agent=agent, action="error", detail=str(exc)[:500]))
            await db.commit()


@router.post("/agents/run")
async def lancer_agent(
    agent: str,
    background: BackgroundTasks,
    _: User | None = Depends(require_admin_access),
):
    """Lance le crawler ou la veille en tâche de fond (réponse immédiate, suivi dans le journal)."""
    if agent not in ("crawl", "veille"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Agent inconnu : crawl | veille")
    background.add_task(_lancer_agent, agent)
    return {
        "lance": agent,
        "message": "Exécution démarrée. La progression apparaît dans le journal des agents "
                   "(plusieurs minutes pour le crawler : les embeddings tournent en local).",
    }


@router.get("/partners")
async def list_all_partners(
    _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Tous les partenaires (candidats compris) pour la revue admin."""
    rows = await db.scalars(select(Partner).order_by(Partner.created_at.desc()))
    return [
        {"id": p.id, "raison_sociale": p.raison_sociale, "siret": p.siret, "email": p.email,
         "rge": p.rge, "zones": p.zones, "metiers": p.metiers, "statut": p.statut,
         "note_moyenne": p.note_moyenne, "charte_signee_at": p.charte_signee_at,
         "created_at": p.created_at}
        for p in rows
    ]


@router.post("/partners/{partner_id}/activate")
async def activate_partner(
    partner_id, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Valide une candidature : statut=actif, charte signée, et génère un mot de passe initial
    (renvoyé UNE seule fois) pour l'accès à l'espace partenaire."""
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire introuvable")

    temp_password = secrets.token_urlsafe(9)
    partner.password_hash = hash_password(temp_password)
    partner.statut = "actif"
    partner.charte_signee_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "id": partner.id,
        "statut": partner.statut,
        "email": partner.email,
        "mot_de_passe_initial": temp_password,  # à transmettre au partenaire, non stocké en clair
    }


@router.post("/partners/{partner_id}/suspend")
async def suspend_partner(
    partner_id, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire introuvable")
    partner.statut = "suspendu"
    await db.commit()
    return {"id": partner.id, "statut": partner.statut}


# --- Signalements de réponses (revue qualité) ---


class TraiterSignalement(BaseModel):
    statut: str
    note_admin: str | None = None


@router.get("/signalements")
async def signalements(
    statut: str | None = None,
    _: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Réponses signalées par les foyers, avec l'échange qui les entoure."""
    stmt = select(MessageReport).order_by(MessageReport.created_at.desc()).limit(200)
    if statut in STATUTS:
        stmt = stmt.where(MessageReport.statut == statut)
    reports = list(await db.scalars(stmt))

    sorties = []
    for r in reports:
        message = await db.get(Message, r.message_id)
        auteur = await db.get(User, r.user_id) if r.user_id else None
        sorties.append(
            {
                "id": str(r.id),
                "motif": r.motif,
                "commentaire": r.commentaire,
                "statut": r.statut,
                "note_admin": r.note_admin,
                "created_at": r.created_at,
                "signale_par": auteur.email if auteur else None,
                "conversation_id": str(message.conversation_id) if message else None,
                "reponse": message.content if message else "(message supprimé)",
                "model_used": message.model_used if message else None,
                "rag_score": round(message.rag_score, 3) if message and message.rag_score is not None else None,
            }
        )
    return sorties


@router.patch("/signalements/{report_id}")
async def traiter_signalement(
    report_id: uuid.UUID,
    payload: TraiterSignalement,
    _: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    if payload.statut not in STATUTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Statut invalide (attendu : {', '.join(STATUTS)})")
    report = await db.get(MessageReport, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Signalement introuvable")
    report.statut = payload.statut
    report.note_admin = payload.note_admin
    await db.commit()
    return {"id": str(report.id), "statut": report.statut}


# --- Foyers & RGPD ---


@router.get("/foyers")
async def rechercher_foyers(
    q: str | None = None,
    _: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Recherche d'un compte par email ou prénom. Sans `q`, renvoie les plus récents."""
    stmt = select(User).order_by(User.created_at.desc()).limit(50)
    if q:
        motif = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(motif), User.prenom.ilike(motif)))
    users = list(await db.scalars(stmt))

    sorties = []
    for u in users:
        nb_conv = await db.scalar(
            select(func.count()).select_from(Conversation).where(Conversation.user_id == u.id)
        )
        sorties.append(
            {
                "id": str(u.id),
                "email": u.email,
                "prenom": u.prenom,
                "created_at": u.created_at,
                "email_verified": u.email_verified,
                "is_admin": u.is_admin,
                "consent_leads": u.consent_leads_at is not None,
                "nb_conversations": nb_conv or 0,
            }
        )
    return sorties


@router.get("/foyers/{user_id}/export")
async def export_foyer(
    user_id: uuid.UUID,
    admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Export RGPD (portabilité) d'un foyer, à sa demande. Réutilise la logique de `account.py`."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable")
    data = await account.export_data(user=user, db=db)
    await _tracer(db, admin, "export_rgpd", user.email)
    return data


@router.delete("/foyers/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_foyer(
    user_id: uuid.UUID,
    admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Droit à l'effacement exercé par l'admin pour le compte d'un foyer. IRRÉVERSIBLE.

    La trace est écrite AVANT la suppression : l'email ne serait plus lisible après.
    """
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable")
    if user.is_admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Un compte administrateur ne se supprime pas ici")
    await _tracer(db, admin, "suppression_rgpd", user.email)
    await account.delete_account(user=user, db=db)


@router.get("/journal-acces")
async def journal_acces(
    limit: int = 100, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Qui a consulté quelles données personnelles, et quand."""
    rows = await db.scalars(select(AdminAccessLog).order_by(AdminAccessLog.created_at.desc()).limit(limit))
    return [
        {"admin": r.admin_email, "action": r.action, "cible": r.cible, "created_at": r.created_at} for r in rows
    ]
