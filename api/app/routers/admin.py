"""Back-office HELIOS.

Deux voies d'accès acceptées (cf. `require_admin_access`) :
- `X-Admin-Token` : secret partagé, pour les scripts et l'outillage en ligne de commande ;
- JWT d'un compte `users.is_admin` : pour l'interface du back-office.

Le back-office est en LECTURE SEULE sur les données des foyers ; les seules écritures sont
les actions explicitement prévues : partenaires (activation / suspension), signalements, et le
suivi des rendez-vous (statut, note interne).

Mises en relation, lot 3 : candidatures (justificatifs, validation avec lien d'activation à
copier, refus motivé), contestations (accepter ou refuser, avec un motif) et justificatifs à
échéance. Chaque action est tracée dans le journal des accès (`_tracer`).
"""
import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session, get_db
from app.core.deps import require_admin_access
from app.models.agent_log import AgentLog
from app.routers import account
from app.models.conversation import Conversation, Message
from app.models.moderation import STATUTS, AdminAccessLog, MessageReport
from app.models.house import House
from app.models.partner import Contestation, Lead, Partner, PartnerDocument
from app.models.rendez_vous import STATUTS_RDV, RendezVous
from app.models.user import User
from app.services import (activation, admin_health, admin_stats, admin_supervision, agents_engine, conformite,
                          conformite_lecture, contestations, justificatifs, rdv_admin, releves, releves_lecture)
from app.services.pdf_releve import releve_pdf
from app.services.creneaux import heure_de_paris


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
    """Tableau de bord : utilisateurs, activité d'Helios, coût IA, business, base de connaissances,
    rendez-vous à venir."""
    tableau = await admin_stats.dashboard(db)
    rdvs = list(await db.scalars(select(RendezVous)))
    tableau["rendez_vous"] = rdv_admin.resume_a_venir(rdvs, datetime.now(timezone.utc))
    if tableau["rendez_vous"]["a_qualifier"]:
        tableau["alertes"].append({"niveau": "action", "texte": (
            f"{tableau['rendez_vous']['a_qualifier']} rendez-vous passé(s) à qualifier (honoré, absent ou annulé)")})
    return tableau


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


async def _partenaire(db: AsyncSession, partner_id) -> Partner:
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partenaire introuvable")
    return partner


@router.get("/partners")
async def list_all_partners(
    _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Tous les partenaires (candidats compris) pour la revue admin, avec leurs justificatifs."""
    rows = list(await db.scalars(select(Partner).order_by(Partner.created_at.desc())))
    charte = await conformite_lecture.charte_en_vigueur(db)
    version = charte.version if charte else None
    docs = await conformite_lecture.documents_par_partenaire(db, (p.id for p in rows))
    jour = date.today()
    return [
        {"id": p.id, "raison_sociale": p.raison_sociale, "siret": p.siret, "email": p.email,
         "rge": p.rge, "zones": p.zones, "metiers": p.metiers, "statut": p.statut, "motif_refus": p.motif_refus,
         "note_moyenne": p.note_moyenne, "charte_signee_at": p.charte_signee_at, "demo": p.demo,
         "charte_version_signee": p.charte_version_signee, "charte_en_vigueur": version,
         "compte_active": p.password_hash is not None,
         "en_regle": conformite.en_regle(bool(p.rge), docs[p.id], p.charte_version_signee, version, jour),
         "justificatifs": {t: e for t, e in conformite.etat_justificatifs(bool(p.rge), docs[p.id], jour).items()},
         "documents": [justificatifs.sortie(d) for d in sorted(docs[p.id], key=lambda d: d.created_at, reverse=True)],
         "created_at": p.created_at}
        for p in rows
    ]


@router.post("/partners/{partner_id}/activate")
async def activate_partner(
    partner_id, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Valide une candidature : statut actif, et un LIEN D'ACTIVATION à usage unique (7 jours) que
    l'administration copie et transmet elle-même — aucun e-mail. Ne signe RIEN à la place du
    partenaire : la charte se signe dans son espace."""
    partner = await _partenaire(db, partner_id)
    if partner.statut == "refuse":
        raise HTTPException(status.HTTP_409_CONFLICT, "Candidature refusée.")
    partner.statut = "actif"
    partner.motif_refus = None
    lien = await activation.creer(db, partner)
    await db.commit()
    await _tracer(db, admin, "partenaire_valide", partner.raison_sociale)
    return {"id": partner.id, "statut": partner.statut, "email": partner.email, **lien}


@router.post("/partners/{partner_id}/lien-activation")
async def nouveau_lien(
    partner_id, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Un nouveau lien (perdu, expiré, mot de passe oublié) ; les précédents cessent de valoir."""
    partner = await _partenaire(db, partner_id)
    if partner.statut != "actif":
        raise HTTPException(status.HTTP_409_CONFLICT, "Seul un partenaire actif reçoit un lien d'activation.")
    lien = await activation.creer(db, partner)
    await db.commit()
    await _tracer(db, admin, "lien_activation", partner.raison_sociale)
    return {"id": partner.id, "email": partner.email, **lien}


class Motif(BaseModel):
    motif: str = Field(min_length=3, max_length=1000)


@router.post("/partners/{partner_id}/refuser")
async def refuser_candidature(
    partner_id, payload: Motif, admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    partner = await _partenaire(db, partner_id)
    if partner.statut != "candidat":
        raise HTTPException(status.HTTP_409_CONFLICT, "Seule une candidature en attente se refuse.")
    partner.statut, partner.motif_refus = "refuse", payload.motif.strip()
    await db.commit()
    await _tracer(db, admin, "candidature_refusee", partner.raison_sociale)
    return {"id": partner.id, "statut": partner.statut, "motif_refus": partner.motif_refus}


@router.get("/partners/{partner_id}/documents/{doc_id}")
async def document_partenaire(
    partner_id, doc_id, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    doc = await db.get(PartnerDocument, doc_id)
    if doc is None or str(doc.partner_id) != str(partner_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    await _tracer(db, admin, "justificatif_lu", f"{doc.type} · {doc.filename}")
    return FileResponse(doc.path, filename=doc.filename)


@router.post("/partners/{partner_id}/documents/{doc_id}/refuser")
async def refuser_document(
    partner_id, doc_id, payload: Motif, admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Un justificatif refusé ne compte plus : le partenaire sort des propositions s'il n'en a pas d'autre."""
    doc = await db.get(PartnerDocument, doc_id)
    if doc is None or str(doc.partner_id) != str(partner_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    doc.statut, doc.motif_refus = "refuse", payload.motif.strip()
    await db.commit()
    await _tracer(db, admin, "justificatif_refuse", f"{doc.type} · {doc.filename}")
    return justificatifs.sortie(doc)


@router.get("/justificatifs/echeances")
async def echeances(
    jours: int = 30, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Justificatifs retenus des partenaires actifs, expirés ou à échéance dans `jours` jours."""
    actifs = list(await db.scalars(select(Partner).where(Partner.statut == "actif")))
    docs = await conformite_lecture.documents_par_partenaire(db, (p.id for p in actifs))
    jour = date.today()
    out = []
    for p in actifs:
        for t, e in conformite.etat_justificatifs(bool(p.rge), docs[p.id], jour).items():
            if e["etat"] == "manquant" or (e["date_fin"] and (e["date_fin"] - jour).days <= jours):
                out.append({"partner_id": p.id, "raison_sociale": p.raison_sociale, "demo": p.demo, "type": t,
                            "libelle": conformite.LIBELLES[t], "etat": e["etat"], "date_fin": e["date_fin"]})
    return sorted(out, key=lambda x: (x["date_fin"] or date.min, x["raison_sociale"]))


# --- Contestations de mises en relation (lot 3) ---


@router.get("/contestations")
async def liste_contestations(
    statut: str = "en_attente", admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    if statut not in ("en_attente", "acceptee", "refusee"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Statut inconnu")
    rows = (await db.execute(
        select(Contestation, Lead, Partner).join(Lead, Contestation.lead_id == Lead.id)
        .join(Partner, Lead.partner_id == Partner.id).where(Contestation.statut == statut)
        .order_by(Contestation.created_at)
    )).all()
    out = []
    for c, lead, partner in rows:
        house = await db.get(House, lead.house_id)
        # Aide au motif « doublon » : la même maison, le même métier, chez ce partenaire, par Hélios
        # dans les 12 mois. Un doublon venu « en direct » reste à l'appréciation de l'administration.
        doublons = await db.scalar(select(func.count()).select_from(Lead).where(
            Lead.house_id == lead.house_id, Lead.partner_id == lead.partner_id, Lead.metier == lead.metier,
            Lead.id != lead.id, Lead.consent_client_at < lead.consent_client_at,
            Lead.consent_client_at >= lead.consent_client_at - timedelta(days=365)))
        out.append({
            "id": c.id, "motif": c.motif, "libelle": contestations.MOTIFS.get(c.motif, c.motif),
            "commentaire": c.commentaire, "essais": c.essais, "statut": c.statut,
            "decision_motif": c.decision_motif, "decidee_le": c.decidee_le, "created_at": c.created_at,
            "lead": {"id": lead.id, "metier": lead.metier, "transmis_le": lead.consent_client_at,
                     "code_postal": house.code_postal if house else None, "creneaux": lead.creneaux or [],
                     "a_un_telephone": lead.contact_telephone is not None, "facturable": lead.facturable,
                     "prix_ht": float(lead.prix_ht) if lead.prix_ht is not None else None},
            "partenaire": {"id": partner.id, "raison_sociale": partner.raison_sociale, "demo": partner.demo},
            "doublons_helios_12_mois": doublons,
        })
    await _tracer(db, admin, "contestations_consultees", statut)
    return out


class Decision(BaseModel):
    acceptee: bool
    motif: str = Field(min_length=3, max_length=1000)


@router.post("/contestations/{contestation_id}/decision")
async def decider_contestation(
    contestation_id, payload: Decision, admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Acceptée → la demande n'est plus facturable (`prix_ht` gardé). Refusée → rien ne change."""
    c = await db.get(Contestation, contestation_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contestation introuvable")
    if c.statut != "en_attente":
        raise HTTPException(status.HTTP_409_CONFLICT, "Contestation déjà tranchée.")
    lead = await db.get(Lead, c.lead_id)
    c.statut = "acceptee" if payload.acceptee else "refusee"
    c.decision_motif, c.decidee_le = payload.motif.strip(), datetime.now(timezone.utc)
    if payload.acceptee:
        lead.facturable = False
    await db.commit()
    await _tracer(db, admin, f"contestation_{c.statut}", str(c.lead_id))
    return {"id": c.id, "statut": c.statut, "facturable": lead.facturable}


@router.post("/partners/{partner_id}/suspend")
async def suspend_partner(
    partner_id, _: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    partner = await _partenaire(db, partner_id)
    partner.statut = "suspendu"
    await db.commit()
    return {"id": partner.id, "statut": partner.statut}


# --- Relevés mensuels (mises en relation, lot 4) — PAS des factures ---


def _mois(mois: str | None) -> str:
    try:
        if mois is None:
            return releves.mois_de(datetime.now(timezone.utc))
        releves.lire_mois(mois)
        return mois
    except releves.MoisInvalide as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/releves")
async def releves_du_mois(
    mois: str | None = None, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Le tableau du mois (par défaut le mois en cours à Paris) : provisoire tant qu'il n'est pas clos."""
    mois = _mois(mois)
    statut, liste = await releves_lecture.releves_du_mois(db, mois)
    cloture = await releves_lecture.cloture(db, mois)
    await _tracer(db, admin, "releves_consultes", mois)
    return {
        "mois": mois, "statut": statut, "cloture_le": cloture.cloture_le if cloture else None,
        "cloture_par": cloture.cloture_par if cloture else None,
        "cloture_possible_le": releves.cloture_possible_le(mois),
        "en_attente": sum(len(r["en_attente"]) for r in liste),
        "total_ht": round(sum(r["total_ht"] for r in liste if not r["partenaire"].get("demo")), 2),
        "releves": liste,
    }


@router.post("/releves/{mois}/cloturer")
async def cloturer_releves(
    mois: str, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Fige le mois pour tous les partenaires : au plus tôt le 8 du mois suivant, sans contestation
    en attente (le refus les nomme). Un relevé clos ne se recalcule plus."""
    mois = _mois(mois)
    try:
        figes = await releves_lecture.cloturer(db, mois, admin.email if admin else "secret_partagé",
                                                pdf=releve_pdf)
    except releves_lecture.ClotureRefusee as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    await _tracer(db, admin, "releves_clos", f"{mois} · {len(figes)} relevé(s)")
    return {"mois": mois, "statut": "clos", "nb_releves": len(figes)}


@router.get("/releves/{mois}/csv")
async def releves_csv(
    mois: str, admin: User | None = Depends(require_admin_access), db: AsyncSession = Depends(get_db)
):
    """Une ligne par mise en relation du mois ; aucune donnée de foyer (code postal seulement)."""
    mois = _mois(mois)
    statut, liste = await releves_lecture.releves_du_mois(db, mois)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["mois", "statut_releve", "partenaire", "siret", "demo", "transmise_le", "heure", "metier",
                "code_postal", "etat", "prix_ht"])
    for r in liste:
        for x in r["lignes"]:
            w.writerow([mois, statut, r["partenaire"]["raison_sociale"], r["partenaire"].get("siret") or "",
                        "oui" if r["partenaire"].get("demo") else "non", x["date"], x["heure"], x["metier"],
                        x["code_postal"] or "", x["etat"], f"{x['prix_ht']:.2f}".replace(".", ",")])
    await _tracer(db, admin, "releves_csv", mois)
    # BOM : Excel lit l'UTF-8 (accents des raisons sociales) seulement s'il le trouve.
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="releves-{mois}.csv"'})


@router.get("/releves/{mois}/{partner_id}/pdf")
async def releve_pdf_admin(
    mois: str, partner_id: uuid.UUID, admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    try:
        contenu, nom = await releves_lecture.pdf_du_mois(db, _mois(mois), partner_id, releve_pdf)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    await _tracer(db, admin, "releve_pdf", mois)
    return Response(contenu, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{nom}"'})




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


# --- Rendez-vous téléphoniques ---


class SuiviRendezVous(BaseModel):
    statut: str | None = None
    note_interne: str | None = None


def _rdv_out(r: RendezVous, foyer_email: str | None) -> dict:
    return {
        "id": str(r.id), "nom": r.nom, "telephone": r.telephone, "email": r.email, "sujet": r.sujet,
        "debut": heure_de_paris(r.debut).isoformat(), "duree_min": r.duree_min, "statut": r.statut,
        "note_interne": r.note_interne, "foyer_email": foyer_email, "created_at": r.created_at,
    }


@router.get("/rendez-vous")
async def rendez_vous(
    periode: str = "a_venir",
    admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Les appels à passer (à venir, du plus proche au plus lointain), ou les 60 derniers jours.

    Noms et téléphones : la consultation est tracée, comme la lecture d'une conversation."""
    if periode not in ("a_venir", "passes"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Période invalide (attendu : a_venir ou passes)")
    rdvs = rdv_admin.filtrer(list(await db.scalars(select(RendezVous))), periode, datetime.now(timezone.utc))
    emails = {u.id: u.email for u in await db.scalars(
        select(User).where(User.id.in_([r.user_id for r in rdvs if r.user_id])))} if rdvs else {}
    await _tracer(db, admin, "rendez_vous_consultes", "à venir" if periode == "a_venir" else "passés")
    return [_rdv_out(r, emails.get(r.user_id)) for r in rdvs]


@router.patch("/rendez-vous/{rdv_id}")
async def suivre_rendez_vous(
    rdv_id: uuid.UUID,
    payload: SuiviRendezVous,
    admin: User | None = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Statut et/ou note interne — modification tracée (qui a marqué « absent », et quand). Un créneau annulé redevient réservable (index partiel, 0029)."""
    r = await db.get(RendezVous, rdv_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rendez-vous introuvable")
    champs = payload.model_dump(exclude_unset=True)
    if "statut" in champs:
        if champs["statut"] not in STATUTS_RDV:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Statut invalide (attendu : {', '.join(STATUTS_RDV)})")
        r.statut = champs["statut"]
    if "note_interne" in champs:
        r.note_interne = (champs["note_interne"] or "").strip()[:4000] or None
    try:
        await db.commit()
    except IntegrityError:
        # Un rendez-vous annulé qu'on réactive alors que son créneau a été repris entre-temps.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Ce créneau a été repris par une autre réservation : impossible de le réactiver.")
    quoi = ", ".join(f"statut {r.statut}" if c == "statut" else "note" for c in champs) or "rien"
    await _tracer(db, admin, "rendez_vous_modifie",
                  f"{r.nom} — {heure_de_paris(r.debut).strftime('%d/%m/%Y %H:%M')} ({quoi})")
    foyer = await db.get(User, r.user_id) if r.user_id else None
    return _rdv_out(r, foyer.email if foyer else None)
