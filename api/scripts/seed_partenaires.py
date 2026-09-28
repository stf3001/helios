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

#: --- NOMS PROVISOIRES, A REMPLACER ---
#: Deux partenaires de plus par metier et par region, demandes par Stephane le 28/09/2026
#: en attendant les vrais. Plutot que d'ecrire 78 raisons sociales a la main, on compose :
#: deux racines locales par region, un mot par metier. Le resultat est lisible, stable
#: d'une execution a l'autre, et se remplace ligne par ligne quand les vrais noms arrivent.
RACINES_REGIONALES: dict[str, tuple[str, str]] = {
    "ara": ("Alpes", "Forez"),
    "bfc": ("Morvan", "Jura"),
    "bre": ("Iroise", "Broceliande"),   # « Armor » est deja pris par ISOLATION_PROVISOIRE
    "cvl": ("Sologne", "Val de Loire"),
    "cor": ("Cinto", "Balagne"),
    "ges": ("Vosges", "Ardenne"),
    "hdf": ("Flandre", "Picardie"),
    "idf": ("Lutece", "Brie"),
    "nor": ("Cotentin", "Pays de Caux"),
    "naq": ("Medoc", "Perigord"),
    "occ": ("Cevennes", "Cerdagne"),
    "pdl": ("Erdre", "Vendee"),
    "pac": ("Luberon", "Esterel"),
}

#: Le mot qui suit la racine, selon le metier.
MOT_DU_METIER = {"solaire": "Solaire", "pac": "Thermique", "isolation": "Isolation"}


def _renforts() -> dict[str, tuple[tuple[str, ...], tuple[str, ...], bool]]:
    """Les deux partenaires supplementaires de chaque metier, dans chaque region.

    La raison sociale est la cle du dictionnaire ET celle du seed : deux entreprises qui
    porteraient le meme nom n'en feraient qu'une, et une region se retrouverait a deux
    partenaires au lieu de trois. C'est arrive une fois, avec « Armor Isolation ». D'ou la
    verification, qui refuse de semer plutot que de laisser un trou passer inapercu.
    """
    lignes: dict[str, tuple[tuple[str, ...], tuple[str, ...], bool]] = {}
    attendus = 0
    for region, (nom_a, nom_b) in RACINES_REGIONALES.items():
        zones = REGIONS[region][1]
        for metier, mot in MOT_DU_METIER.items():
            for racine in (nom_a, nom_b):
                lignes[f"{racine} {mot}"] = (zones, (metier,), True)
                attendus += 1
    collisions = attendus - len(lignes)
    if collisions or set(lignes) & set(ISOLATION_PROVISOIRE.values()):
        doublons = sorted(set(lignes) & set(ISOLATION_PROVISOIRE.values()))
        raise ValueError(
            f"raisons sociales en double ({collisions} perdue(s)) : {doublons or 'entre renforts'}"
        )
    return lignes


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
    **_renforts(),
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
