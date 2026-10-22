"""Dépôt d'un justificatif partenaire (Kbis, décennale, RGE) — mises en relation, lot 3.

Utilisé par la candidature publique ET par l'espace partenaire : mêmes règles aux deux endroits.
Fichiers sous `generated/partner_docs/<partner_id>/` (gitignoré).
"""
import uuid
from datetime import date
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.models.partner import Partner, PartnerDocument
from app.services import conformite

DOCS_DIR = Path(__file__).resolve().parents[2] / "generated" / "partner_docs"
MAX_SIZE = 10 * 1024 * 1024
ALLOWED_CT = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
EXTENSIONS = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def verifier_dates(type_: str, date_delivrance: date | None, date_fin: date | None, aujourd_hui: date) -> None:
    if type_ not in conformite.TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Type de justificatif inconnu.")
    if type_ == "kbis" and not conformite.kbis_recent(date_delivrance, aujourd_hui):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "L'extrait Kbis doit dater de moins de 3 mois : indiquez sa date de délivrance.")
    if type_ in conformite.AVEC_DATE_FIN and (date_fin is None or date_fin < aujourd_hui):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"{conformite.LIBELLES[type_]} : indiquez une date de fin de validité à venir.")


async def lire_fichier(fichier: UploadFile) -> bytes:
    if fichier.content_type not in ALLOWED_CT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Format non accepté (PDF ou image uniquement).")
    contenu = await fichier.read()
    if len(contenu) > MAX_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Fichier trop volumineux (10 Mo au plus).")
    if not contenu:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Fichier vide.")
    return contenu


def ecrire(partner: Partner, type_: str, nom: str, content_type: str, contenu: bytes,
           date_delivrance: date | None, date_fin: date | None) -> PartnerDocument:
    """Écrit le fichier et renvoie le document à ajouter à la session (l'appelant committe)."""
    dossier = DOCS_DIR / str(partner.id)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{uuid.uuid4()}{EXTENSIONS[content_type]}"
    chemin.write_bytes(contenu)
    return PartnerDocument(partner_id=partner.id, type=type_, filename=nom or chemin.name, path=str(chemin),
                           date_delivrance=date_delivrance if type_ == "kbis" else None,
                           date_fin=date_fin if type_ in conformite.AVEC_DATE_FIN else None)


def sortie(d: PartnerDocument) -> dict:
    return {"id": d.id, "type": d.type, "filename": d.filename, "date_delivrance": d.date_delivrance,
            "date_fin": d.date_fin, "statut": d.statut, "motif_refus": d.motif_refus, "created_at": d.created_at}
