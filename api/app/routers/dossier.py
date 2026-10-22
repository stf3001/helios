"""Carnet de maison, lot 6 : le « Dossier de la maison » en PDF, gratuit, pour le foyer connecté.

Généré à la demande et renvoyé tel quel : rien n'est conservé sur le disque. Les moteurs des
lots 1 à 4 calculent ici (âges, garanties, échéances, journal fusionné) ; `pdf_dossier` ne
fait que mettre en forme.
"""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.ratelimit import limiter
from app.models.equipement import Equipement
from app.models.house_document import HouseDocument
from app.models.isolant import Isolant
from app.models.journal import JournalEntree
from app.models.piece import Emetteur, Piece
from app.models.travaux import Travaux
from app.models.user import User
from app.routers.equipements import _own_house
from app.services.a_faire import derniers_faits, journal_fusionne
from app.services.entretien import echeances, table_courante
from app.services.garanties import age_ans, fin_garanties_chantier, statut_garantie
from app.services.pdf_dossier import SECTIONS, dossier_pdf
from app.services.pieces import resume_pieces

router = APIRouter(prefix="/houses/me/dossier", tags=["carnet"])


class DemandeDossier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[str] = Field(default_factory=lambda: list(SECTIONS))
    numeros_serie: bool = False  # exclus par défaut (décision de Stéphane)


@router.post("")
@limiter.limit("10/minute")
async def telecharger_dossier(request: Request, payload: DemandeDossier,
                              user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    aujourd_hui = date.today()
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    travaux = list(await db.scalars(select(Travaux).where(Travaux.house_id == house.id)))
    isolants = list(await db.scalars(select(Isolant).where(Isolant.house_id == house.id).order_by(Isolant.created_at)))
    entrees = list(await db.scalars(select(JournalEntree).where(JournalEntree.house_id == house.id)))
    pieces = list(await db.scalars(
        select(Piece).where(Piece.house_id == house.id).order_by(Piece.niveau, Piece.ordre, Piece.created_at)))
    emetteurs = list(await db.scalars(
        select(Emetteur).where(Emetteur.piece_id.in_([p.id for p in pieces])))) if pieces else []
    # Les photos de pièce sont des documents comme les autres dans la liste.
    documents = list(await db.scalars(
        select(HouseDocument).where(HouseDocument.house_id == house.id).order_by(HouseDocument.uploaded_at)))

    eqs = []
    for e in equipements:
        age, statut = age_ans(e, aujourd_hui)
        eqs.append({**{c.name: getattr(e, c.name) for c in e.__table__.columns}, "age_ans": age, "age_statut": statut})
    chantiers = []
    for t in sorted(travaux, key=lambda t: (t.date_reception or date.min), reverse=True):
        garanties = [{**g, "statut": statut_garantie(g["fin"], aujourd_hui)}
                     for g in (fin_garanties_chantier(t.date_reception) if t.date_reception else [])]
        chantiers.append({**{c.name: getattr(t, c.name) for c in t.__table__.columns}, "garanties": garanties,
                          "isolants": [i for i in isolants if i.travaux_id == t.id]})

    contenu = dossier_pdf(
        house=house, equipements=eqs, travaux=chantiers, pieces=pieces, emetteurs=emetteurs,
        resume=resume_pieces(house, pieces, emetteurs) if pieces else None,
        echeances=echeances(equipements, table_courante()["taches"], derniers_faits(entrees), aujourd_hui, maison=house),
        journal=journal_fusionne(entrees, travaux), documents=documents,
        sections=[s for s in payload.sections if s in SECTIONS], numeros_serie=payload.numeros_serie,
        aujourd_hui=aujourd_hui,
    )
    nom = f"dossier-maison-{aujourd_hui.isoformat()}.pdf"
    return Response(contenu, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{nom}"'})
