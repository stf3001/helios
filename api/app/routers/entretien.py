"""Carnet de maison, lots 3 et 4 : échéances d'entretien, « C'est fait », bloc « À faire ».

Ni rappel ni e-mail ici : quand le fournisseur sera branché (point 1 de TODO.md), les
rappels liront `a_faire_de_la_maison` — la même chose que le bloc de l'espace.
Le journal fournit `derniers_faits` : une tâche cochée fait avancer son échéance.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.equipement import Equipement
from app.models.house import House
from app.models.journal import JournalEntree
from app.models.partner import Lead, Partner
from app.models.risques import RisquesCommune
from app.models.travaux import Travaux
from app.models.user import User
from app.routers.equipements import _own_house
from app.routers.journal import cols, verifier_liens, verifier_limite
from app.schemas.journal import Fait
from app.services import risques_affichage, suivi_foyer
from app.services.a_faire import a_faire, derniers_faits
from app.services.entretien import echeances, table_courante, verifications
from app.services.garanties import garanties_maison
from app.services.parcours import garanties_visibles, parcours

router = APIRouter(prefix="/houses/me", tags=["carnet"])


async def _calcul(db: AsyncSession, house: House) -> dict:
    table = table_courante()
    equipements = list(await db.scalars(select(Equipement).where(Equipement.house_id == house.id)))
    entrees = list(await db.scalars(select(JournalEntree).where(JournalEntree.house_id == house.id)))
    return {
        "table": table,
        "equipements": equipements,
        "echeances": echeances(equipements, table["taches"], derniers_faits(entrees), date.today(), maison=house),
        "verifications": verifications(table["taches"], house),
    }


@router.get("/entretien")
async def get_entretien(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    c = await _calcul(db, house)
    return {
        "version": c["table"]["version"],
        "avertissement": c["table"]["avertissement"],
        "taches_validees": len(c["table"]["taches"]),
        # L'écran en a besoin pour dire « calendrier en préparation » plutôt que « rien à faire ».
        "table_vide": not c["table"]["taches"],
        "echeances": c["echeances"],
        # Sans date : « Vérifiez si votre terrain est concerné » quand la fiche dit « ne sais pas ».
        "verifications": c["verifications"],
    }


async def a_faire_de_la_maison(db: AsyncSession, house: House) -> dict:
    c = await _calcul(db, house)
    travaux = list(await db.scalars(select(Travaux).where(Travaux.house_id == house.id)))
    garanties = garanties_visibles(garanties_maison(c["equipements"], travaux, date.today()), house)
    bloc = a_faire(c["echeances"], garanties, date.today(), table_vide=not c["table"]["taches"])
    bloc["sans_equipement"] = not any(e.en_service for e in c["equipements"])
    # Lot 8 : l'écran choisit d'après le profil (acheteur → « Avant d'acheter » à la place du bloc).
    bloc["parcours"] = parcours(house)
    # Mises en relation, lot 5 : « L'entreprise vous a-t-elle contacté ? » tant qu'elle attend sa réponse.
    leads = (await db.execute(select(Lead, Partner.raison_sociale).join(Partner, Partner.id == Lead.partner_id)
                              .where(Lead.house_id == house.id, Lead.type == "travaux"))).all()
    bloc["questions_contact"] = [
        {"lead_id": l.id, "partenaire": nom, "metier": l.metier, "transmis_le": l.consent_client_at}
        for l, nom in leads if suivi_foyer.question_contact_due(l, date.today())]
    # Phase 2 : feux de forêt dans la commune et débroussaillement « ne sais pas » → l'invitation
    # du calendrier remonte ici. Cache seulement : jamais d'appel à Géorisques pour ce bloc.
    ligne = await db.get(RisquesCommune, house.code_insee) if house.code_insee else None
    bloc["debroussaillement"] = (risques_affichage.section(ligne, house, c["verifications"])["debroussaillement"]
                                 if ligne is not None else None)
    bloc["rien_d_urgent"] = bloc["rien_d_urgent"] and not bloc["questions_contact"] and not bloc["debroussaillement"]
    return bloc


@router.get("/a-faire")
async def get_a_faire(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    return await a_faire_de_la_maison(db, house)


@router.post("/entretien/{tache_id}/fait", status_code=status.HTTP_201_CREATED)
async def marquer_fait(tache_id: str, payload: Fait, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    house = await _own_house(db, user.id)
    tache = next((t for t in table_courante()["taches"] if t["id"] == tache_id), None)
    if tache is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tâche d'entretien inconnue")
    de_maison = "maison" in tache["applique_a"]
    if de_maison and payload.equipement_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cette tâche concerne la maison, pas un équipement")
    if not de_maison and payload.equipement_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Précisez l'équipement entretenu")
    champs = payload.model_dump()
    await verifier_liens(db, house, champs)
    await verifier_limite(db, house)
    e = JournalEntree(house_id=house.id, type="entretien", titre=tache["libelle"][:120], tache_id=tache_id, **champs)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return cols(e)
