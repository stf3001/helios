"""Deux mises en relation de DÉMONSTRATION pour vérifier le suivi côté foyer (lot 5).

Sur la maison du compte de démo, aux seuls partenaires « Démo … » :
- Démo Soleil du Var, solaire, transmise le 13/10/2026 à 10 h, sans aucun contact déclaré : plus de
  5 jours ouvrés après, la question « L'entreprise vous a-t-elle contacté ? » est due ;
- Démo Isolation Azur, isolation, transmise le 08/10/2026 ; le partenaire déclare un contact le 09/10,
  le foyer répond « non » : un ÉCART de contact, et une demande signalée sans contact.

Marquées par leur message ; relancé, le script les remet à l'état initial.
Lancer depuis `api/` : `.venv/Scripts/python.exe -m scripts.seed_suivi_demo`
"""

import asyncio
from datetime import date, datetime, timezone

from sqlalchemy import delete, select

from app.core.db import async_session
from app.models.house import House
from app.models.partner import Lead, Partner
from app.models.user import User
from app.services.creneaux import a_paris

MARQUE = "Demande de démonstration (suivi foyer, lot 5)"


async def semer() -> None:
    async with async_session() as db:
        maison = await db.scalar(select(House).join(User, User.id == House.user_id)
                                 .where(User.email == "demo@helios.fr"))
        if maison is None:
            raise SystemExit("Compte de démo sans maison.")
        await db.execute(delete(Lead).where(Lead.message == MARQUE))

        async def partenaire(nom):
            p = await db.scalar(select(Partner).where(Partner.raison_sociale == nom, Partner.demo.is_(True)))
            if p is None:
                raise SystemExit(f"{nom} absent : lancer d'abord `scripts.seed_partenaires_demo`.")
            return p
        soleil, azur = await partenaire("Démo Soleil du Var"), await partenaire("Démo Isolation Azur")
        db.add_all([
            Lead(house_id=maison.id, partner_id=soleil.id, type="travaux", metier="solaire", statut="transmis",
                 consent_client_at=a_paris(2026, 10, 13, 10), prix_ht=60, message=MARQUE,
                 creneaux=[{"jour": "mardi", "plage": "soir"}]),
            Lead(house_id=maison.id, partner_id=azur.id, type="travaux", metier="isolation", statut="contacte",
                 consent_client_at=a_paris(2026, 10, 8, 9), prix_ht=60, message=MARQUE, contacte_le=date(2026, 10, 9),
                 contact_foyer="non", contact_foyer_le=datetime(2026, 10, 19, 9, tzinfo=timezone.utc),
                 sans_contact_signale=True),
        ])
        await db.commit()
    print("2 demandes de démonstration posées (question due, écart de contact).")


if __name__ == "__main__":
    asyncio.run(semer())
