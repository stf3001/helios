r"""Remplit l'annuaire des partenaires, region par region.

Idempotent : relancer le script met a jour les zones et les metiers d'un partenaire deja
present plutot que de le dupliquer. La raison sociale sert de cle.

    .venv\Scripts\python.exe -m scripts.seed_partenaires

ATTENTION — LA PLUPART DE CES RAISONS SOCIALES SONT PROVISOIRES. Stephane a demande de
remplir l'annuaire avec des noms quelconques en attendant les vrais. Ces entreprises
N'EXISTENT PAS : les treize isolations, les soixante-dix-huit renforts et le courtier.
Seules cinq sont reelles (AD Solar, Ensol, Hydrolia, Eolia, Energiesto).

C'est pourquoi le seed ne les active PAS : elles entrent en `en_attente`, statut que
l'annuaire public filtre et que `routers/chat.py` ne donne pas au modele. Helios ne nomme
donc que les vraies, et dit franchement qu'il n'a pas encore de partenaire dans la region
— ce qui vaut mieux qu'envoyer un client chez une societe inventee, ou que de faire
decouvrir a une vraie societe homonyme qu'elle est « partenaire HELIOS ». On les repasse
en `actif` une par une, a la signature.
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
    # Quatre acteurs nationaux : ils vendent en ligne ou a distance, donc toutes zones.
    "Hydrolia": (TOUS_DEPARTEMENTS, ("eau",), False),
    "Eolia": (TOUS_DEPARTEMENTS, ("eolien",), False),
    "Energiesto": (TOUS_DEPARTEMENTS, ("inertie",), False),
    # Le courtage ne demande aucun deplacement : un contrat se renegocie sur dossier.
    # NOM PROVISOIRE, choisi par Stephane en attendant de signer un vrai courtier.
    "France Courtage": (TOUS_DEPARTEMENTS, ("courtage",), False),
    **{
        nom: (REGIONS[region][1], ("isolation",), True)
        for region, nom in ISOLATION_PROVISOIRE.items()
    },
    **_renforts(),
}

#: Les cinq entreprises reelles. Tout le reste de `PARTENAIRES` est provisoire et reste
#: `en_attente` jusqu'a signature. Liste en dur et non deduite : une raison sociale qui
#: n'y figure pas est inventee par defaut, ce qui est le sens prudent de l'erreur.
REELS: frozenset[str] = frozenset({"AD Solar", "Ensol", "Hydrolia", "Eolia", "Energiesto"})


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
            partenaire.statut = "actif" if raison_sociale in REELS else "en_attente"
        await db.commit()

        actifs = list(await db.scalars(select(Partner).where(Partner.statut == "actif")))
        provisoires = len(PARTENAIRES) - len(REELS)
        print(
            f"{len(PARTENAIRES)} partenaires semes ({provisoires} provisoires laisses "
            f"en attente), {len(actifs)} actifs dans l'annuaire."
        )

        # Le seed ne connait que SES lignes. Des partenaires actifs peuvent venir d'ailleurs :
        # un ancien seed, une candidature validee, un test. Le 06/10/2026 il en restait quatre,
        # tous inventes (« Armor Solaire » et « Armor Thermique » d'un nommage abandonne,
        # « Solaris Renov » et « Courtage Energie Pro » des tests du jalon 8) — et le chat les
        # nommait. On ne les desactive PAS d'office, pour ne pas defaire une activation faite
        # a la main depuis /admin ; on les affiche, pour qu'ils ne repassent pas inapercus.
        inconnus = sorted(p.raison_sociale for p in actifs if p.raison_sociale not in REELS)
        if inconnus:
            print(
                f"ATTENTION : {len(inconnus)} partenaire(s) actif(s) hors de ce script — "
                f"verifier qu'ils existent vraiment : {', '.join(inconnus)}"
            )


if __name__ == "__main__":
    asyncio.run(semer())
