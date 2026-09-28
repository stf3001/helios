r"""Remplit l'annuaire des partenaires, region par region.

Idempotent : relancer le script met a jour les zones et les metiers d'un partenaire deja
present plutot que de le dupliquer. La raison sociale sert de cle.

    .venv\Scripts\python.exe -m scripts.seed_partenaires

ATTENTION — LES PARTENAIRES ISOLATION SONT DES NOMS PROVISOIRES. Stephane a demande de
remplir la colonne avec des noms quelconques en attendant les vrais. Ces treize
entreprises N'EXISTENT PAS. Elles doivent etre remplacees avant toute mise en relation
reelle : envoyer un client chez une societe inventee serait pire que de ne rien proposer.
Elles sont regroupees ci-dessous pour qu'on les trouve d'un coup d'oeil.
"""

import asyncio

from sqlalchemy import select

from app.core.db import async_session
from app.models.partner import Partner
from app.services.regions import REGIONS, TOUS_DEPARTEMENTS

DEPTS_PACA = REGIONS["pac"][1]
DEPTS_HORS_PACA = tuple(d for d in TOUS_DEPARTEMENTS if d not in DEPTS_PACA)

#: --- NOMS PROVISOIRES, A REMPLACER --- (cf. l'avertissement en tete de fichier)
ISOLATION_PROVISOIRE: dict[str, str] = {
    "ara": "Isolation des Volcans",
    "bfc": "Thermibourgogne",
    "bre": "Armor Isolation",
    "cvl": "Isoval Centre",
    "cor": "Isolation Cismonte",
    "ges": "Vosg'Isol",
    "hdf": "Isolation des Flandres",
    "idf": "Parisol Renovation",
    "nor": "Normandie Calfeutrage",
    "naq": "Atlantic Isolation",
    "occ": "Isolation du Lauragais",
    "pdl": "Loire Isolation",
    "pac": "Isolation Mistral",
}

#: raison sociale -> (zones, metiers, rge)
PARTENAIRES: dict[str, tuple[tuple[str, ...], tuple[str, ...], bool]] = {
    # Le seul partenaire a couvrir PACA sur le solaire et la pompe a chaleur.
    "AD Solar": (DEPTS_PACA, ("solaire", "pac"), True),
    # Partout ailleurs.
    "Ensol": (DEPTS_HORS_PACA, ("solaire", "pac"), True),
    # Trois acteurs nationaux : ils vendent en ligne, donc toutes zones.
    "Hydrolia": (TOUS_DEPARTEMENTS, ("eau",), False),
    "Eolia": (TOUS_DEPARTEMENTS, ("eolien",), False),
    "Energiesto": (TOUS_DEPARTEMENTS, ("inertie",), False),
    **{
        nom: (REGIONS[region][1], ("isolation",), True)
        for region, nom in ISOLATION_PROVISOIRE.items()
    },
}


async def semer() -> None:
    async with async_session() as db:
        for raison_sociale, (zones, metiers, rge) in PARTENAIRES.items():
            partenaire = await db.scalar(
                select(Partner).where(Partner.raison_sociale == raison_sociale)
            )
            if partenaire is None:
                partenaire = Partner(raison_sociale=raison_sociale)
                db.add(partenaire)
            partenaire.zones = list(zones)
            partenaire.metiers = list(metiers)
            partenaire.rge = rge
            partenaire.statut = "actif"
        await db.commit()

        total = len(list(await db.scalars(select(Partner).where(Partner.statut == "actif"))))
        print(f"{len(PARTENAIRES)} partenaires semes, {total} actifs dans l'annuaire.")


if __name__ == "__main__":
    asyncio.run(semer())
