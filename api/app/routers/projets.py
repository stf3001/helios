"""Carnet, lot 9 : les projets de la maison — de l'idée à la réception des travaux.

Ce routeur ne calcule AUCUN chiffre. `lier-etude` recopie celui d'un calcul existant
(simulateur, pré-audit) ; le foyer peut déclarer le montant d'un devis ; c'est tout.
`terminer` remplit le carnet en une seule transaction : chantier (et donc garanties),
équipements cochés par le foyer, entrée de journal, projet clos. Une erreur annule tout.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.audit import Audit
from app.models.equipement import MAX_EQUIPEMENTS_PAR_MAISON, Equipement
from app.models.house import House
from app.models.house_document import HouseDocument
from app.models.journal import JournalEntree
from app.models.kb import KbDocument
from app.models.projet import Projet
from app.models.simulateur import SimulateurStudy
from app.models.travaux import MAX_TRAVAUX_PAR_MAISON, Travaux
from app.models.user import User
from app.routers.equipements import _own_house, _synchroniser
from app.routers.journal import verifier_limite
from app.routers.travaux import _verifier_documents
from app.services import projets as pj
from app.services.agents_engine import SOURCES
from app.services.parcours import parcours

router = APIRouter(prefix="/houses/me/projets", tags=["carnet"])

LIENS_OUTILS = {"simulateur-solaire": "/simulateur-solaire", "vent": "/le-vent", "jardin": "/espace/jardin",
                "pre-audit": "/espace/audits", "aucun": None}


class ProjetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modele_id: str = Field(max_length=60)


class ProjetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titre: str | None = Field(default=None, min_length=1, max_length=120)
    etape: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    devis_document_ids: list[uuid.UUID] | None = Field(default=None, max_length=10)
    # Le montant d'un devis reçu : DÉCLARÉ par le foyer, il remplace le budget de l'étude.
    devis_montant_eur: float | None = Field(default=None, ge=0, le=10_000_000)


class Terminer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date_reception: date
    entreprise: str | None = Field(default=None, max_length=120)
    montant_ttc: float | None = Field(default=None, ge=0, le=10_000_000)
    facture_document_id: uuid.UUID | None = None
    attestation_assurance_document_id: uuid.UUID | None = None
    # Les rangs des équipements proposés par le modèle que le foyer a cochés.
    equipements: list[int] = Field(default_factory=list, max_length=10)


def _lien(outil: str) -> str | None:
    return LIENS_OUTILS["pre-audit" if outil.startswith("pre-audit:") else outil]


def _modeles() -> dict[str, dict]:
    return {m["id"]: m for m in pj.charger_modeles()}


def _sources() -> set[str]:
    return {s.name for s in SOURCES}


async def _own_projet(db: AsyncSession, house: House, projet_id: uuid.UUID) -> Projet:
    p = await db.get(Projet, projet_id)
    if p is None or p.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projet introuvable")
    return p


async def _derniere_etude(db: AsyncSession, house: House, modele: dict) -> dict | None:
    """Le calcul le plus récent de l'outil du modèle, recopié tel quel (ou None)."""
    outil = modele["outil"]
    if outil == "simulateur-solaire":
        for e in await db.scalars(select(SimulateurStudy).where(SimulateurStudy.house_id == house.id)
                                  .order_by(SimulateurStudy.created_at.desc())):
            r = pj.depuis_simulateur(e.resultat or {}, modele["poste"], e.created_at, e.id)
            if r:
                return r
    elif outil.startswith("pre-audit:"):
        for a in await db.scalars(select(Audit).where(Audit.house_id == house.id).order_by(Audit.created_at.desc())):
            r = pj.depuis_audit(a.json_result or {}, outil.split(":", 1)[1], a.created_at, a.id)
            if r:
                return r
    return None


async def _fiches(db: AsyncSession, sources: list[str]) -> list[dict]:
    """Les questions de chaque fiche, pour que l'écran y renvoie (« Avant de signer »)."""
    rows = (await db.execute(select(KbDocument.source, KbDocument.titre)
                             .where(KbDocument.source.in_(sources), KbDocument.statut == "actif")
                             .order_by(KbDocument.titre))).all()
    return [{"source": s, "questions": [t for src, t in rows if src == s]} for s in sources]


def _out(p: Projet, modele: dict | None) -> dict:
    sortie = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    sortie["modele"] = None if modele is None else {
        "titre": modele["titre"], "famille": modele["famille"], "outil": modele["outil"],
        "outil_lien": _lien(modele["outil"]), "fiches_kb": modele["fiches_kb"],
        "equipements_crees": modele["equipements_crees"],
    }
    return sortie


@router.get("/modeles")
async def get_modeles(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    visibles = pj.modeles_visibles(list(_modeles().values()), house, parcours(house), _sources())
    sortie = []
    for m in visibles:
        etude = await _derniere_etude(db, house, m)
        sortie.append({
            "id": m["id"], "titre": m["titre"], "famille": m["famille"], "outil": m["outil"],
            "outil_lien": _lien(m["outil"]),
            # « Une étude solaire du 12/10 existe » : ce qui est déjà calculé pour ce modèle.
            "calcul": None if etude is None else {"type": etude["etude_ref"]["type"], "date": etude["etude_ref"]["date"]},
        })
    return {"familles": list(pj.FAMILLES), "modeles": sortie}


@router.get("")
async def list_projets(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    modeles = _modeles()
    rows = await db.scalars(select(Projet).where(Projet.house_id == house.id).order_by(Projet.created_at))
    return [_out(p, modeles.get(p.modele_id)) for p in rows]


@router.get("/{projet_id}")
async def get_projet(projet_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_projet(db, house, projet_id)
    modele = _modeles().get(p.modele_id)
    sortie = _out(p, modele)
    sortie["fiches"] = await _fiches(db, modele["fiches_kb"]) if modele else []
    return sortie


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_projet(payload: ProjetCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    visibles = {m["id"]: m for m in pj.modeles_visibles(list(_modeles().values()), house, parcours(house), _sources())}
    modele = visibles.get(payload.modele_id)
    if modele is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce projet n'est pas proposé pour votre logement")
    nb = await db.scalar(select(func.count()).select_from(Projet).where(Projet.house_id == house.id))
    if nb >= pj.MAX_PROJETS_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Limite de {pj.MAX_PROJETS_PAR_MAISON} projets atteinte — supprimez-en un pour en ajouter un.")
    p = Projet(house_id=house.id, modele_id=modele["id"], titre=modele["titre"], etape="idee")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _out(p, modele)


@router.patch("/{projet_id}")
async def update_projet(projet_id: uuid.UUID, payload: ProjetUpdate, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_projet(db, house, projet_id)
    champs = payload.model_dump(exclude_unset=True)
    if p.etape == "termine" and set(champs) - {"note"}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un projet terminé ne change plus : seule sa note reste modifiable.")
    if "etape" in champs and champs["etape"] not in pj.ETAPES_LIBRES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Étape inconnue — « terminé » passe par « Les travaux sont terminés ».")
    for doc_id in champs.get("devis_document_ids") or []:
        doc = await db.get(HouseDocument, doc_id)
        if doc is None or doc.house_id != house.id or doc.type != "devis":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Seuls vos documents de type « devis » se joignent ici.")
    if "devis_montant_eur" in champs:
        montant = champs.pop("devis_montant_eur")
        p.budget_bas_eur = p.budget_haut_eur = montant
        p.budget_source, p.budget_statut = ("devis", "declare") if montant is not None else (None, None)
        p.budget_date = date.today() if montant is not None else None
    if "devis_document_ids" in champs:
        champs["devis_document_ids"] = [str(d) for d in champs["devis_document_ids"] or []]
    for champ, valeur in champs.items():
        if champ in ("titre", "etape") and valeur is None:
            continue
        setattr(p, champ, valeur)
    await db.commit()
    await db.refresh(p)
    return _out(p, _modeles().get(p.modele_id))


@router.delete("/{projet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_projet(projet_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_projet(db, house, projet_id)
    await db.delete(p)  # le chantier d'un projet terminé reste au carnet (SET NULL)
    await db.commit()


@router.post("/{projet_id}/lier-etude")
async def lier_etude(projet_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_projet(db, house, projet_id)
    if p.etape == "termine":
        raise HTTPException(status.HTTP_409_CONFLICT, "Un projet terminé ne change plus.")
    modele = _modeles().get(p.modele_id)
    if modele and modele["outil"] == "aucun":
        raise HTTPException(status.HTTP_409_CONFLICT, "Pas de calculateur pour ce projet : lisez les fiches qui l'accompagnent.")
    etude = await _derniere_etude(db, house, modele) if modele else None
    if etude is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun calcul pour ce projet : faites-le d'abord avec l'outil.")
    # Tels quels : un budget déclaré d'après un devis est remplacé par celui de l'étude, que le
    # foyer vient de demander ; il le redéclarera s'il le souhaite.
    for champ, valeur in etude.items():
        setattr(p, champ, date.fromisoformat(valeur) if champ.endswith("_date") and valeur else valeur)
    await db.commit()
    await db.refresh(p)
    return _out(p, modele)


async def _ecrire_journal(db: AsyncSession, house: House, p: Projet, payload: Terminer) -> None:
    await verifier_limite(db, house)
    db.add(JournalEntree(house_id=house.id, date=payload.date_reception, type="amelioration", titre=p.titre[:120],
                         intervenant=payload.entreprise, cout_eur=payload.montant_ttc,
                         document_id=payload.facture_document_id))


@router.post("/{projet_id}/terminer")
async def terminer(projet_id: uuid.UUID, payload: Terminer, user: User = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    p = await _own_projet(db, house, projet_id)
    if p.etape in ("termine", "abandonne"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce projet est déjà clos.")
    if payload.date_reception > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La date de réception ne peut pas être dans le futur.")
    modele = _modeles().get(p.modele_id) or {"equipements_crees": []}
    try:
        a_creer = pj.equipements_a_creer(modele, payload.equipements)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await _verifier_documents(db, house, payload.model_dump())
    nb_travaux = await db.scalar(select(func.count()).select_from(Travaux).where(Travaux.house_id == house.id))
    if nb_travaux >= MAX_TRAVAUX_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limite de {MAX_TRAVAUX_PAR_MAISON} chantiers atteinte.")
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    if len(equipements) + len(a_creer) > MAX_EQUIPEMENTS_PAR_MAISON:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limite de {MAX_EQUIPEMENTS_PAR_MAISON} équipements atteinte.")

    # Rien n'est validé avant le commit final : la moindre erreur ci-dessous annule tout.
    t = Travaux(house_id=house.id, nature=p.titre[:120], entreprise=payload.entreprise,
                date_reception=payload.date_reception, montant_ttc=payload.montant_ttc,
                facture_document_id=payload.facture_document_id,
                attestation_assurance_document_id=payload.attestation_assurance_document_id)
    db.add(t)
    await db.flush()
    for e in a_creer:
        origine = e.get("origine_fiche")
        if origine:
            # Le nouvel appareil prend la place de celui qui la tenait : l'ancien passe dans
            # les anciens équipements, la fiche suit le nouveau (lot 7).
            for ancien in equipements:
                if ancien.en_service and ancien.origine_fiche == origine:
                    ancien.en_service = False
        db.add(Equipement(house_id=house.id, categorie=e["categorie"], type=e["type"], origine_fiche=origine,
                          date_pose=payload.date_reception, installateur=payload.entreprise, travaux_id=t.id))
    await db.flush()
    await _synchroniser(db, house)
    await _ecrire_journal(db, house, p, payload)
    p.etape, p.travaux_id = "termine", t.id
    await db.commit()
    await db.refresh(p)
    return _out(p, _modeles().get(p.modele_id))
