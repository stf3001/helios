"""Endpoints admin — validation des candidatures partenaires (doc 08 §5).

Protégés par un secret partagé (header X-Admin-Token = settings.admin_token). Suffisant en v1 ;
à remplacer par un vrai back-office authentifié si le volume le justifie.
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_admin
from app.core.security import hash_password
from app.models.agent_log import AgentLog
from app.models.partner import Partner

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/agents-log")
async def agents_log(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Journal des agents (crawler + veille) — supervision de l'alimentation du RAG (doc 10)."""
    rows = await db.scalars(select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit))
    return [{"agent": r.agent, "action": r.action, "detail": r.detail, "created_at": r.created_at} for r in rows]


@router.get("/partners")
async def list_all_partners(db: AsyncSession = Depends(get_db)):
    """Tous les partenaires (candidats compris) pour la revue admin."""
    rows = await db.scalars(select(Partner).order_by(Partner.created_at.desc()))
    return [
        {"id": p.id, "raison_sociale": p.raison_sociale, "siret": p.siret, "email": p.email,
         "rge": p.rge, "zones": p.zones, "metiers": p.metiers, "statut": p.statut}
        for p in rows
    ]


@router.post("/partners/{partner_id}/activate")
async def activate_partner(partner_id, db: AsyncSession = Depends(get_db)):
    """Valide une candidature : statut=actif, charte signée, et génère un mot de passe initial
    (renvoyé UNE seule fois) pour l'accès à l'espace partenaire."""
    from datetime import datetime, timezone

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
async def suspend_partner(partner_id, db: AsyncSession = Depends(get_db)):
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire introuvable")
    partner.statut = "suspendu"
    await db.commit()
    return {"id": partner.id, "statut": partner.statut}
