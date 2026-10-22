"""Espace partenaire — doc 04. Le partenaire se connecte, lit ses demandes et déclare leur suivi.

Mises en relation à prix fixe (série 4, lot 1) : aucune commission sur un lead `travaux`, le prix
est figé à la création (`prix_ht`) ; le courtage (`energie`) garde son calcul.

Lot 2 : le partenaire lit le dossier transmis (`GET /partner/leads/{id}`), figé au consentement,
avec son score expliqué ligne par ligne, les créneaux en tête et les coordonnées — en lecture
seule. Après un retrait de consentement, il ne reste rien à lire.

Lot 3 :
- suivi DÉCLARATIF (contacté avec sa date, devis et signé avec un montant facultatif, perdu avec
  un motif) : statistiques et information du foyer, JAMAIS d'effet sur le prix ni la facturabilité ;
- contestation dans les 7 jours (`services/contestations.py`), tranchée par l'administration ;
- « Mon entreprise » : justificatifs (`services/justificatifs.py`) et signature de la charte en
  vigueur. Un partenaire qui n'est pas en règle (`services/conformite.py`) sort des propositions
  mais garde l'accès à ses demandes ;
- activation du compte par un lien à usage unique (`services/activation.py`), sans e-mail.
"""
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_partner
from app.core.ratelimit import limiter
from app.core.security import create_partner_token, hash_password, verify_password
from app.models.house import House
from app.models.partner import Contestation, Lead, Partner, PartnerDocument
from app.routers.leads import LEAD_DOCS_DIR
from app.services import (activation, commission, conformite, conformite_lecture, contestations, justificatifs,
                          releves, releves_lecture)
from app.services.pdf_releve import releve_pdf

# Le partenaire n'appelle que parce que le foyer l'a demandé, dans les créneaux qu'il a donnés.
RAPPEL_LEGAL = ("Ce foyer a demandé à être contacté au sujet de ce projet. Appelez-le uniquement dans les "
                "créneaux indiqués : le démarchage téléphonique est interdit pour les travaux de rénovation "
                "énergétique (art. L. 223-1 du code de la consommation, loi n° 2020-901). Sans téléphone, "
                "écrivez-lui.")

router = APIRouter(prefix="/partner", tags=["partner"])


class PartnerLogin(BaseModel):
    email: str
    password: str


@router.post("/login")
async def partner_login(payload: PartnerLogin, db: AsyncSession = Depends(get_db)):
    partner = await db.scalar(select(Partner).where(Partner.email == payload.email))
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    if partner is None or not partner.password_hash or partner.statut != "actif":
        raise invalid
    if not verify_password(payload.password, partner.password_hash):
        raise invalid
    return {"access_token": create_partner_token(str(partner.id)), "raison_sociale": partner.raison_sociale}


# --- Activation du compte (lien à usage unique, sans e-mail) ---


class Activer(BaseModel):
    jeton: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=200)


async def _activation_valide(db: AsyncSession, jeton: str):
    a = await activation.trouver(db, jeton)
    if not activation.utilisable(a, datetime.now(timezone.utc)):
        raise HTTPException(status.HTTP_410_GONE, "Ce lien d'activation n'est plus valable : demandez-en un nouveau.")
    partner = await db.get(Partner, a.partner_id)
    if partner is None or partner.statut != "actif":
        raise HTTPException(status.HTTP_410_GONE, "Ce lien d'activation n'est plus valable : demandez-en un nouveau.")
    return a, partner


@router.get("/activation")
@limiter.limit("20/minute")
async def lire_activation(request: Request, jeton: str, db: AsyncSession = Depends(get_db)):
    _, partner = await _activation_valide(db, jeton)
    return {"raison_sociale": partner.raison_sociale, "email": partner.email}


@router.post("/activation")
@limiter.limit("10/minute")
async def activer(request: Request, payload: Activer, db: AsyncSession = Depends(get_db)):
    a, partner = await _activation_valide(db, payload.jeton)
    a.utilise_le = datetime.now(timezone.utc)
    partner.password_hash = hash_password(payload.password)
    await db.commit()
    return {"access_token": create_partner_token(str(partner.id)), "raison_sociale": partner.raison_sociale}


# --- Mes demandes ---


async def _lead_du_partenaire(db: AsyncSession, partner: Partner, lead_id) -> Lead:
    lead = await db.get(Lead, lead_id)
    if lead is None or lead.partner_id != partner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead introuvable")
    return lead


async def _contestations(db: AsyncSession, lead_ids) -> dict:
    ids = list(lead_ids)
    if not ids:
        return {}
    return {c.lead_id: c for c in await db.scalars(select(Contestation).where(Contestation.lead_id.in_(ids)))}


def _contestation_out(c: Contestation | None) -> dict | None:
    if c is None:
        return None
    return {"motif": c.motif, "libelle": contestations.MOTIFS.get(c.motif, c.motif), "commentaire": c.commentaire,
            "essais": c.essais, "statut": c.statut, "decision_motif": c.decision_motif, "decidee_le": c.decidee_le,
            "created_at": c.created_at}


def _suivi(lead: Lead, contestation: Contestation | None, maintenant: datetime) -> dict:
    return {
        "statut": lead.statut, "contacte_le": lead.contacte_le, "montant_travaux": lead.montant_travaux,
        "motif_perdu": lead.motif_perdu, "facturable": lead.facturable,
        "prix_ht": float(lead.prix_ht) if lead.prix_ht is not None else None,
        "fin_contestation": contestations.fin_delai(lead.consent_client_at),
        "peut_contester": contestations.peut_contester(lead, maintenant, [contestation] if contestation else []),
        "contestation": _contestation_out(contestation),
    }


@router.get("/leads")
async def my_leads(partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Du plus récent au plus ancien ; données client minimales (code postal), le reste au dossier."""
    leads = list(await db.scalars(
        select(Lead).where(Lead.partner_id == partner.id).order_by(Lead.created_at.desc())
    ))
    contests = await _contestations(db, (l.id for l in leads))
    maintenant = datetime.now(timezone.utc)
    out = []
    for lead in leads:
        house = await db.get(House, lead.house_id)
        out.append({
            "id": lead.id, "type": lead.type, "metier": lead.metier,
            "code_postal": house.code_postal if house else None,
            "commission": float(lead.commission) if lead.commission is not None else None,  # historique, courtage
            "consent_retire": lead.consent_retire_at is not None,
            "score": lead.score, "creneaux": lead.creneaux or [],
            "created_at": lead.created_at,
            **_suivi(lead, contests.get(lead.id), maintenant),
        })
    return out


@router.get("/leads/{lead_id}")
async def lead_detail(lead_id, partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Le dossier transmis, tel qu'il a été figé au consentement : créneaux en tête."""
    lead = await _lead_du_partenaire(db, partner, lead_id)
    contests = await _contestations(db, [lead.id])
    return {
        "id": lead.id, "metier": lead.metier, "created_at": lead.created_at,
        "consent_client_at": lead.consent_client_at, "consent_retire": lead.consent_retire_at is not None,
        "creneaux": lead.creneaux or [],
        "contact": {"nom": lead.contact_nom, "telephone": lead.contact_telephone, "email": lead.contact_email},
        "message": lead.message,
        "score": lead.score, "score_detail": lead.score_detail or [],
        "dossier": lead.dossier,
        "rappel_legal": RAPPEL_LEGAL,
        **_suivi(lead, contests.get(lead.id), datetime.now(timezone.utc)),
    }


@router.get("/leads/{lead_id}/documents/{doc_id}")
async def lead_document(lead_id, doc_id, partner: Partner = Depends(get_current_partner),
                        db: AsyncSession = Depends(get_db)):
    """La COPIE faite au consentement — jamais le document de la maison lui-même."""
    lead = await _lead_du_partenaire(db, partner, lead_id)
    docs = {d["id"]: d for d in ((lead.dossier or {}).get("documents") or [])}
    doc = docs.get(str(doc_id))
    copies = list((LEAD_DOCS_DIR / str(lead.id)).glob(f"{doc_id}.*")) if doc else []
    if not copies:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    return FileResponse(copies[0], filename=doc["filename"])


class Suivi(BaseModel):
    """Suivi déclaratif : sans effet sur le prix ni la facturabilité."""
    statut: Literal["contacte", "devis", "signe", "perdu"]
    contacte_le: date | None = None
    montant_travaux: int | None = Field(default=None, ge=0)
    motif_perdu: str | None = Field(default=None, max_length=1000)


@router.patch("/leads/{lead_id}/status")
async def advance_lead(
    lead_id, payload: Suivi, partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db),
):
    lead = await _lead_du_partenaire(db, partner, lead_id)
    if lead.statut == "signe":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead signé : immuable.")
    if lead.consent_retire_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Consentement retiré par le client : lead inexploitable.")
    if payload.statut == "contacte":
        jour = payload.contacte_le or date.today()
        if jour > date.today() or jour < lead.consent_client_at.date():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La date de contact doit suivre la transmission, sans dépasser aujourd'hui.")
        lead.contacte_le = jour
    if payload.statut == "perdu":
        if not (payload.motif_perdu or "").strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Indiquez pourquoi le projet est sans suite.")
        lead.motif_perdu = payload.motif_perdu.strip()
    if payload.montant_travaux is not None and payload.statut in ("devis", "signe"):
        lead.montant_travaux = payload.montant_travaux

    lead.statut = payload.statut
    if payload.statut == "signe" and lead.type != "travaux":
        lead.commission = commission.compute_commission(lead.metier, lead.montant_travaux)
    await db.commit()
    return {"id": lead.id, "statut": lead.statut, "contacte_le": lead.contacte_le,
            "montant_travaux": lead.montant_travaux, "facturable": lead.facturable}


class Contester(BaseModel):
    motif: str = Field(max_length=30)
    commentaire: str = Field(max_length=2000)
    essais: list[date] = Field(default_factory=list, max_length=10)


@router.post("/leads/{lead_id}/contestation", status_code=status.HTTP_201_CREATED)
async def contester(lead_id, payload: Contester, partner: Partner = Depends(get_current_partner),
                    db: AsyncSession = Depends(get_db)):
    lead = await _lead_du_partenaire(db, partner, lead_id)
    existantes = list((await _contestations(db, [lead.id])).values())
    refus = contestations.refus(lead, datetime.now(timezone.utc), existantes, payload.motif, payload.commentaire,
                                payload.essais)
    if refus:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, refus)
    c = Contestation(lead_id=lead.id, motif=payload.motif, commentaire=payload.commentaire.strip(),
                     essais=[d.isoformat() for d in sorted(payload.essais)] if payload.motif == "injoignable" else None)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _contestation_out(c)


# --- Mon entreprise : justificatifs et charte ---


@router.get("/me")
async def mon_entreprise(partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    charte = await conformite_lecture.charte_en_vigueur(db)
    version = charte.version if charte else None
    docs = (await conformite_lecture.documents_par_partenaire(db, [partner.id]))[partner.id]
    jour = date.today()
    return {
        "raison_sociale": partner.raison_sociale, "email": partner.email, "siret": partner.siret,
        "zones": partner.zones or [], "metiers": partner.metiers or [], "rge": partner.rge,
        "lien_interet": partner.lien_interet,
        "en_regle": conformite.en_regle(bool(partner.rge), docs, partner.charte_version_signee, version, jour),
        "alertes": conformite.alertes(bool(partner.rge), docs, partner.charte_version_signee, version, jour),
        "justificatifs": {t: {**e, "libelle": conformite.LIBELLES[t]}
                          for t, e in conformite.etat_justificatifs(bool(partner.rge), docs, jour).items()},
        "documents": [justificatifs.sortie(d) for d in sorted(docs, key=lambda d: d.created_at, reverse=True)],
        "charte": {"version": version, "texte": charte.texte if charte else None,
                   "version_signee": partner.charte_version_signee, "signee_le": partner.charte_signee_at},
    }


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def deposer(
    type: str = Form(...), fichier: UploadFile = File(...),
    date_delivrance: date | None = Form(None), date_fin: date | None = Form(None),
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db),
):
    justificatifs.verifier_dates(type, date_delivrance, date_fin, date.today())
    contenu = await justificatifs.lire_fichier(fichier)
    doc = justificatifs.ecrire(partner, type, fichier.filename or "", fichier.content_type, contenu,
                               date_delivrance, date_fin)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return justificatifs.sortie(doc)


@router.get("/documents/{doc_id}")
async def telecharger(doc_id, partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    doc = await db.get(PartnerDocument, doc_id)
    if doc is None or doc.partner_id != partner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    return FileResponse(doc.path, filename=doc.filename)


class Signer(BaseModel):
    version: str = Field(max_length=20)


@router.post("/charte")
async def signer_charte(payload: Signer, partner: Partner = Depends(get_current_partner),
                        db: AsyncSession = Depends(get_db)):
    """Signe la charte EN VIGUEUR : la version envoyée doit être celle que le partenaire a lue."""
    charte = await conformite_lecture.charte_en_vigueur(db)
    if charte is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Aucune charte n'est en vigueur pour l'instant.")
    if payload.version != charte.version:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La charte en vigueur est la {charte.version} : relisez-la.")
    partner.charte_version_signee = charte.version
    partner.charte_signee_at = datetime.now(timezone.utc)
    await db.commit()
    return {"version_signee": partner.charte_version_signee, "signee_le": partner.charte_signee_at}


# --- Mes relevés (lot 4) — pas des factures ---


@router.get("/releves")
async def mes_releves(partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Un mois par mois où une mise en relation à prix fixe a été transmise, du plus récent au plus ancien."""
    transmis = await db.scalars(select(Lead.consent_client_at).where(
        Lead.partner_id == partner.id, Lead.type == "travaux", Lead.prix_ht.is_not(None)))
    out = []
    for mois in sorted({releves.mois_de(t) for t in transmis}, reverse=True):
        statut, liste = await releves_lecture.releves_du_mois(db, mois, partner.id)
        if liste:
            out.append({"statut": statut, **liste[0]})
    return out


@router.get("/releves/{mois}/pdf")
async def mon_releve_pdf(mois: str, partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)):
    """Même règle que l'administration : le PDF figé si le mois est clos, « provisoire » sinon."""
    try:
        releves.lire_mois(mois)
        contenu, nom = await releves_lecture.pdf_du_mois(db, mois, partner.id, releve_pdf)
    except releves.MoisInvalide as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    return Response(contenu, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{nom}"'})
