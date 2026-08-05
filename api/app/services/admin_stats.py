"""Agrégations du back-office — lecture seule, aucun effet de bord.

Séparé du router pour rester testable sans HTTP. Toutes les valeurs viennent de la base :
aucune estimation, aucun chiffre inventé (règle projet, doc 07 §6).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.models.house import House
from app.models.kb import KbDocument
from app.models.partner import Lead, Partner
from app.models.user import User


def _since(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _start_of_day() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month() -> datetime:
    return datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def _count(db: AsyncSession, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    if conditions:
        stmt = stmt.where(*conditions)
    return await db.scalar(stmt) or 0


async def utilisateurs(db: AsyncSession) -> dict:
    total = await _count(db, User)
    return {
        "total": total,
        "nouveaux_7j": await _count(db, User, User.created_at >= _since(7)),
        "nouveaux_30j": await _count(db, User, User.created_at >= _since(30)),
        "email_verifie": await _count(db, User, User.email_verified.is_(True)),
        "avec_fiche": await db.scalar(select(func.count(func.distinct(House.user_id)))) or 0,
        # Complétude moyenne des fiches existantes (None si aucune fiche : on n'invente pas un 0).
        "completude_moyenne": round(await db.scalar(select(func.avg(House.completeness_score))) or 0, 1),
        "consent_leads": await _count(db, User, User.consent_leads_at.is_not(None)),
    }


async def activite_helios(db: AsyncSession) -> dict:
    """Activité du chat sur 7 jours + répartition par voie de réponse.

    `model_used` : "kb" = réponse instantanée (aucun LLM), "local" = Ollama, "api" = Claude.
    Le ratio instantané/local/api pilote directement le coût et la latence.
    """
    repartition = dict(
        (row[0] or "inconnu", row[1])
        for row in (
            await db.execute(
                select(Message.model_used, func.count())
                .where(Message.role == "helios", Message.created_at >= _since(7))
                .group_by(Message.model_used)
            )
        ).all()
    )
    return {
        "conversations_7j": await _count(db, Conversation, Conversation.started_at >= _since(7)),
        "conversations_total": await _count(db, Conversation),
        "messages_7j": await _count(db, Message, Message.created_at >= _since(7)),
        "mode_connecte_7j": await _count(
            db, Conversation, Conversation.started_at >= _since(7), Conversation.mode == "connecte"
        ),
        "repartition_7j": repartition,
        # Questions dont la meilleure source est restée sous le seuil de pertinence :
        # ce sont les trous de la base de connaissances.
        "sans_reponse_7j": await _count(
            db,
            Message,
            Message.role == "helios",
            Message.created_at >= _since(7),
            Message.rag_score.is_not(None),
            Message.rag_score < settings.rag_score_threshold,
        ),
    }


async def cout_ia(db: AsyncSession) -> dict:
    """Coût réel des appels API (Claude), rapporté aux plafonds configurés."""
    jour = await db.scalar(
        select(func.coalesce(func.sum(Message.estimated_cost_eur), 0.0)).where(Message.created_at >= _start_of_day())
    )
    mois = await db.scalar(
        select(func.coalesce(func.sum(Message.estimated_cost_eur), 0.0)).where(Message.created_at >= _start_of_month())
    )
    appels_api_mois = await _count(
        db, Message, Message.model_used == "api", Message.created_at >= _start_of_month()
    )
    return {
        "jour_eur": round(jour or 0, 4),
        "mois_eur": round(mois or 0, 4),
        "plafond_jour_eur": settings.llm_api_budget_daily_eur,
        "plafond_mois_eur": settings.llm_api_budget_monthly_eur,
        "appels_api_mois": appels_api_mois,
        "modele": settings.llm_api_model,
        "cle_configuree": bool(settings.llm_api_key),
        "quota_par_client_jour": settings.llm_api_daily_requests_per_user,
    }


async def business(db: AsyncSession) -> dict:
    """Pipeline partenaires/leads + commissions. `commission` est en Numeric → cast float."""
    par_statut = dict(
        (row[0], row[1])
        for row in (await db.execute(select(Lead.statut, func.count()).group_by(Lead.statut))).all()
    )
    commissions_mois = await db.scalar(
        select(func.coalesce(func.sum(Lead.commission.cast(Float)), 0.0)).where(
            Lead.statut == "signe", Lead.created_at >= _start_of_month()
        )
    )
    return {
        "partenaires_actifs": await _count(db, Partner, Partner.statut == "actif"),
        "candidatures_en_attente": await _count(db, Partner, Partner.statut == "candidat"),
        "leads_total": await _count(db, Lead),
        "leads_par_statut": par_statut,
        "commissions_signees_mois_eur": round(commissions_mois or 0, 2),
        "consentements_retires": await _count(db, Lead, Lead.consent_retire_at.is_not(None)),
    }


async def base_connaissances(db: AsyncSession) -> dict:
    par_source = dict(
        (row[0], row[1])
        for row in (
            await db.execute(
                select(KbDocument.source, func.count())
                .where(KbDocument.statut == "actif")
                .group_by(KbDocument.source)
            )
        ).all()
    )
    return {
        "fiches_actives": await _count(db, KbDocument, KbDocument.statut == "actif"),
        "fiches_obsoletes": await _count(db, KbDocument, KbDocument.statut == "obsolete"),
        "par_source": dict(sorted(par_source.items(), key=lambda kv: -kv[1])),
        "sources": len(par_source),
    }


def alertes(cout: dict, biz: dict, kb: dict) -> list[dict]:
    """Signaux à traiter, dérivés des agrégats — pas de requête supplémentaire."""
    out: list[dict] = []
    if cout["plafond_mois_eur"] and cout["mois_eur"] >= 0.8 * cout["plafond_mois_eur"]:
        out.append({"niveau": "alerte", "texte": f"Budget IA du mois à {cout['mois_eur']:.2f} € / {cout['plafond_mois_eur']} €"})
    if cout["plafond_jour_eur"] and cout["jour_eur"] >= 0.8 * cout["plafond_jour_eur"]:
        out.append({"niveau": "alerte", "texte": f"Budget IA du jour à {cout['jour_eur']:.2f} € / {cout['plafond_jour_eur']} €"})
    if not cout["cle_configuree"]:
        out.append({"niveau": "info", "texte": "Aucune clé API configurée : Helios répond uniquement en local (mode simplifié)."})
    if biz["candidatures_en_attente"]:
        out.append({"niveau": "action", "texte": f"{biz['candidatures_en_attente']} candidature(s) partenaire à examiner"})
    if biz["consentements_retires"]:
        out.append({"niveau": "info", "texte": f"{biz['consentements_retires']} consentement(s) client retiré(s)"})
    if kb["fiches_obsoletes"]:
        out.append({"niveau": "action", "texte": f"{kb['fiches_obsoletes']} fiche(s) de connaissance marquée(s) obsolète(s)"})
    return out


async def dashboard(db: AsyncSession) -> dict:
    users = await utilisateurs(db)
    activite = await activite_helios(db)
    cout = await cout_ia(db)
    biz = await business(db)
    kb = await base_connaissances(db)
    return {
        "utilisateurs": users,
        "activite": activite,
        "cout_ia": cout,
        "business": biz,
        "base_connaissances": kb,
        "alertes": alertes(cout, biz, kb),
        "genere_a": datetime.now(timezone.utc).isoformat(),
    }
