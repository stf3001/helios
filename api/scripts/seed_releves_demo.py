"""Mises en relation de DÉMONSTRATION datées de septembre 2026, pour vérifier les relevés (lot 4).

Octobre ne peut pas être clos avant le 8 novembre : pour montrer un relevé CLOS, il faut un mois
passé. Ce script pose, sur la maison du compte de démo et aux seuls partenaires « Démo … »
(`seed_partenaires_demo`), quelques demandes transmises en septembre 2026 :

- Démo Isolation Azur : une facturable (04/09), une contestée puis REFUSÉE (12/09, comptée), une
  contestée puis ACCEPTÉE (18/09, non due), et une le 30/09 à 23 h 30 à Paris (la frontière du mois) ;
- Démo Thermique Maures : une facturable (10/09).

Elles sont closes côté suivi (signé / sans suite) pour ne pas occuper les places « en cours » du
foyer de démo, et marquées par leur message. Idempotent tant que septembre n'est pas clos ;
une fois clos, il refuse de toucher au mois (un relevé clos ne bouge plus).
Lancer depuis `api/` : `.venv/Scripts/python.exe -m scripts.seed_releves_demo`
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.core.db import async_session
from app.models.house import House
from app.models.partner import Contestation, Lead, Partner, ReleveCloture
from app.models.user import User
from app.services.creneaux import a_paris

MARQUE = "Demande de démonstration (relevés, lot 4)"
MOIS = "2026-09"
DEMANDES = [  # (partenaire, jour, heure, minute, métier, contestation, statut)
    ("Démo Isolation Azur", 4, 10, 0, "isolation", None, "signe"),
    ("Démo Isolation Azur", 12, 15, 0, "pac", "refusee", "perdu"),
    ("Démo Isolation Azur", 18, 9, 30, "solaire", "acceptee", "perdu"),
    ("Démo Isolation Azur", 30, 23, 30, "isolation", None, "perdu"),
    ("Démo Thermique Maures", 10, 11, 0, "isolation", None, "signe"),
]


async def semer() -> None:
    async with async_session() as db:
        if await db.get(ReleveCloture, MOIS) is not None:
            raise SystemExit(f"{MOIS} est clos : ses relevés sont figés, rien n'est modifié.")
        maison = await db.scalar(select(House).join(User, User.id == House.user_id)
                                 .where(User.email == "demo@helios.fr"))
        if maison is None:
            raise SystemExit("Compte de démo sans maison.")
        anciens = list(await db.scalars(select(Lead.id).where(Lead.message == MARQUE)))
        if anciens:
            await db.execute(delete(Contestation).where(Contestation.lead_id.in_(anciens)))
            await db.execute(delete(Lead).where(Lead.id.in_(anciens)))
        for nom, jour, h, mi, metier, contestation, statut in DEMANDES:
            p = await db.scalar(select(Partner).where(Partner.raison_sociale == nom, Partner.demo.is_(True)))
            if p is None:
                raise SystemExit(f"{nom} absent : lancer d'abord `scripts.seed_partenaires_demo`.")
            transmis = a_paris(2026, 9, jour, h, mi)
            lead = Lead(house_id=maison.id, partner_id=p.id, type="travaux", metier=metier, statut=statut,
                        consent_client_at=transmis, prix_ht=60, message=MARQUE,
                        facturable=contestation != "acceptee", contacte_le=transmis.date())
            db.add(lead)
            await db.flush()
            if contestation:
                db.add(Contestation(lead_id=lead.id, motif="doublon", commentaire="Démonstration", statut=contestation,
                                    decision_motif="Démonstration", decidee_le=datetime.now(timezone.utc)))
        await db.commit()
    print(f"{len(DEMANDES)} demandes de démonstration posées en {MOIS}.")


if __name__ == "__main__":
    asyncio.run(semer())
