"""Les regions metropolitaines et leurs departements.

Pourquoi ici : un partenaire se pense en REGION (« Ensol couvre l'Occitanie ») mais
l'annuaire filtre en DEPARTEMENT, parce qu'un visiteur donne un code postal, pas une
region. Cette table fait le lien, une fois pour toutes.

Elle ne bouge pas : c'est du decoupage administratif, pas un reglage. Corse comprise,
outre-mer exclu — le perimetre annonce est la France metropolitaine.
"""

#: code region -> (nom affiche, departements couverts)
REGIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "ara": ("Auvergne-Rhone-Alpes",
            ("01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74")),
    "bfc": ("Bourgogne-Franche-Comte",
            ("21", "25", "39", "58", "70", "71", "89", "90")),
    "bre": ("Bretagne", ("22", "29", "35", "56")),
    "cvl": ("Centre-Val de Loire", ("18", "28", "36", "37", "41", "45")),
    "cor": ("Corse", ("2A", "2B")),
    "ges": ("Grand Est",
            ("08", "10", "51", "52", "54", "55", "57", "67", "68", "88")),
    "hdf": ("Hauts-de-France", ("02", "59", "60", "62", "80")),
    "idf": ("Ile-de-France", ("75", "77", "78", "91", "92", "93", "94", "95")),
    "nor": ("Normandie", ("14", "27", "50", "61", "76")),
    "naq": ("Nouvelle-Aquitaine",
            ("16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87")),
    "occ": ("Occitanie",
            ("09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82")),
    "pdl": ("Pays de la Loire", ("44", "49", "53", "72", "85")),
    "pac": ("Provence-Alpes-Cote d'Azur", ("04", "05", "06", "13", "83", "84")),
}

#: Les metiers que l'annuaire distingue. `eau`, `eolien` et `inertie` sont servis par un
#: seul acteur national chacun : ils couvrent toutes les zones.
METIERS = ("solaire", "pac", "isolation", "eau", "eolien", "inertie")

TOUS_DEPARTEMENTS: tuple[str, ...] = tuple(
    d for _, departements in REGIONS.values() for d in departements
)


def region_du_departement(departement: str) -> str | None:
    """La region d'un departement, ou None s'il n'est pas metropolitain."""
    cible = departement.upper()
    for code, (_, departements) in REGIONS.items():
        if cible in departements:
            return code
    return None


def departement_du_code_postal(code_postal: str) -> str | None:
    """Le departement d'un code postal. La Corse a ses deux lettres, d'ou le cas a part."""
    code = (code_postal or "").strip()
    if len(code) < 2 or not code[:2].isdigit():
        return None
    if code.startswith("20"):
        # 20000-20190 et 20600-20620 -> Corse-du-Sud / Haute-Corse. Le decoupage reel est
        # plus fin ; on tranche au milieu, faute de table officielle embarquee.
        return "2A" if code < "20200" else "2B"
    return code[:2]
