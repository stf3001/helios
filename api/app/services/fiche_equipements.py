"""Carnet, lot 7 : l'équipement en service est la source, la fiche Maison en est la copie.

Depuis le lot 1, le type et l'année des systèmes vivaient à deux endroits — la fiche
(lue par le pré-audit et le score de complétude) et l'équipement du carnet. Ici une seule
table de correspondance dit, pour chaque `origine_fiche`, quels champs de fiche un
équipement détermine et comment son code se traduit.

Fonctions PURES : la route leur passe la maison et ses équipements, elles ne lisent ni
n'écrivent rien. Le pré-audit n'est pas touché — il continue de lire la fiche.

RÈGLE QUI TIENT TOUT : on n'écrit JAMAIS dans la fiche une valeur que l'équipement ne dit
pas. Un type d'équipement sans équivalent dans la fiche (une eau chaude ou une ventilation
« autre ») ne détermine donc rien : la fiche reste libre, ni verrouillée ni vidée — le foyer
peut avoir une solution que le carnet ne sait pas nommer.
"""
from datetime import date

# origine_fiche → (champ de type, champ d'année). La clim n'a pas d'année dans la fiche.
CHAMPS_PAR_ORIGINE: dict[str, tuple[str, str | None]] = {
    "chauffage_principal": ("chauffage_principal", "chauffage_principal_annee"),
    "chauffage_appoint": ("chauffage_appoint", "chauffage_appoint_annee"),
    "ecs": ("ecs", "ecs_annee"),
    "clim": ("clim_type", None),
    "ventilation": ("ventilation", None),
}

# Type d'équipement (`models/equipement.py`) → valeur de la fiche (`schemas/house.py`).
# `None` = aucun équivalent, la fiche reste libre. Sens inverse de `_TYPE_CHAUFFAGE` de
# `suggestions_fiche.py` : plusieurs types d'appareils tombent sur le même code de fiche.
_VERS_FICHE: dict[str, dict[str, str | None]] = {
    "chauffage": {
        "PAC_air_eau": "PAC_air_eau", "PAC_air_air": "PAC_air_air",
        "chaudiere_gaz": "gaz", "chaudiere_fioul": "fioul",
        "chaudiere_bois": "bois", "poele_bois": "bois", "poele_granules": "bois", "insert": "bois",
        "convecteurs": "elec_direct", "radiateurs_inertie": "elec_direct",
        "autre": "autre",
    },
    "ecs": {
        "ballon_elec": "ballon_elec", "thermodynamique": "thermodynamique", "gaz": "gaz",
        "solaire": "solaire", "instantane": "instantane",
        "autre": None,  # la fiche n'a pas d'« autre » pour l'eau chaude
    },
    "ventilation": {
        "VMC_simple": "VMC_simple", "VMC_double": "VMC_double",
        "autre": None,  # ni pour la ventilation : `aucune` et `naturelle` ne sont pas un appareil
    },
    # La fiche ne connaît la climatisation que par un texte libre : on y écrit le libellé du
    # type. RECOPIE DE `components/carnet/libelles.ts` — les deux se tiennent à jour ENSEMBLE.
    "clim": {
        "split": "Split", "multisplit": "Multisplit", "gainable": "Gainable",
        "PAC_air_air": "PAC air/air réversible", "autre": "Autre",
    },
}

# Décision 1 : un chauffage « autre » ne réécrit pas une fiche qui dit déjà la même chose.
# `reseau` se traduit en `autre` à l'aller (lot 1) : la fiche n'a donc rien de faux à dire
# qu'un équipement « autre » remplacerait. Le champ reste verrouillé pour autant.
_EQUIVALENTS_AUTRE: dict[str, tuple[str, ...]] = {
    "chauffage_principal": ("reseau", "autre"),
    "chauffage_appoint": ("reseau", "autre"),
}


def _champ(obj, nom):
    """Lit un attribut d'un modèle SQLAlchemy comme une clé de dict (tests, scripts)."""
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def annee_pose(equipement) -> int | None:
    """L'année de pose : celle de la date exacte si elle existe, sinon l'année déclarée."""
    exacte = _champ(equipement, "date_pose")
    if isinstance(exacte, date):
        return exacte.year
    return _champ(equipement, "annee_pose")


def valeur_fiche(origine: str, categorie: str | None, type_: str | None) -> str | None:
    """La valeur de fiche qu'un type d'équipement détermine, ou `None` s'il n'y en a pas."""
    if origine not in CHAMPS_PAR_ORIGINE or not type_:
        return None
    table = _VERS_FICHE.get("clim" if origine == "clim" else (categorie or ""))
    return table.get(type_) if table else None


def champs_verrouilles_de(origine: str) -> tuple[str, ...]:
    """Les champs de fiche qu'un équipement de cette origine tient en lecture seule.

    La clim verrouille `clim` et `clim_type`, jamais `clim_nb_pieces` : le nombre de pièces
    climatisées n'est pas une propriété de l'appareil, le foyer continue de le saisir.
    """
    champ_type, champ_annee = CHAMPS_PAR_ORIGINE[origine]
    champs = ["clim", champ_type] if origine == "clim" else [champ_type]
    if champ_annee:
        champs.append(champ_annee)
    return tuple(champs)


def champs_fiche_depuis(equipement) -> dict:
    """Ce que cet équipement impose à la fiche. Vide s'il ne lui impose rien.

    Un équipement hors service, sans `origine_fiche`, ou dont le type n'a pas d'équivalent
    dans la fiche ne détermine rien. L'année suit la RÈGLE STRICTE : un équipement sans date
    met l'année de fiche à vide, car c'est lui qui dit la vérité (la migration 0030 a d'abord
    recopié l'année de la fiche dans ces équipements, une fois pour toutes).
    """
    origine = _champ(equipement, "origine_fiche")
    if origine not in CHAMPS_PAR_ORIGINE or _champ(equipement, "en_service") is False:
        return {}
    valeur = valeur_fiche(origine, _champ(equipement, "categorie"), _champ(equipement, "type"))
    if valeur is None:
        return {}
    champ_type, champ_annee = CHAMPS_PAR_ORIGINE[origine]
    champs: dict = {champ_type: valeur}
    if origine == "clim":
        champs["clim"] = True
    if champ_annee:
        champs[champ_annee] = annee_pose(equipement)
    return champs


def champs_a_vider(origine: str) -> dict:
    """Ce qu'il reste de la fiche quand l'appareil part sans remplaçant : rien.

    `clim` repasse à `False` — plus d'appareil, plus de climatisation ; `clim_nb_pieces`
    n'est pas touché, il appartient au foyer.
    """
    champ_type, champ_annee = CHAMPS_PAR_ORIGINE[origine]
    champs: dict = {champ_type: None}
    if origine == "clim":
        champs["clim"] = False
    if champ_annee:
        champs[champ_annee] = None
    return champs


def equipement_de_la_fiche(equipements, origine: str):
    """L'unique équipement EN SERVICE portant cette origine, s'il existe."""
    for e in equipements:
        if _champ(e, "origine_fiche") == origine and _champ(e, "en_service") is not False:
            return e
    return None


def champs_verrouilles(equipements) -> list[str]:
    """Les champs de fiche que le carnet tient à jour : l'écran les affiche en lecture.

    Un champ est verrouillé dès qu'un équipement en service porte son origine ET que son
    type a un équivalent dans la fiche — sinon personne ne le renseignerait plus.
    """
    champs: list[str] = []
    for origine in CHAMPS_PAR_ORIGINE:
        eq = equipement_de_la_fiche(equipements, origine)
        if eq is not None and valeur_fiche(origine, _champ(eq, "categorie"), _champ(eq, "type")) is not None:
            champs += [c for c in champs_verrouilles_de(origine) if c not in champs]
    return champs


def valeurs_attendues(equipements) -> dict:
    """Tout ce que les équipements en service imposent à la fiche, champ par champ."""
    attendues: dict = {}
    for origine in CHAMPS_PAR_ORIGINE:
        eq = equipement_de_la_fiche(equipements, origine)
        if eq is not None:
            attendues.update(champs_fiche_depuis(eq))
    return attendues


def ecarts(maison, equipements) -> list[dict]:
    """Les champs où la fiche contredit l'équipement, avec les deux valeurs.

    Sert à la migration 0030 (l'équipement gagne, l'ancienne valeur part au journal) et au
    refus d'un `PATCH /houses/me` qui changerait un champ verrouillé. Un chauffage « autre »
    face à un réseau de chaleur n'est PAS un écart (décision 1) : la fiche dit déjà `autre`
    à la traduction, il n'y a rien à corriger.
    """
    sortie = []
    for champ, attendue in valeurs_attendues(equipements).items():
        actuelle = _champ(maison, champ)
        if actuelle == attendue:
            continue
        if attendue == "autre" and actuelle in _EQUIVALENTS_AUTRE.get(champ, ()):
            continue
        sortie.append({"champ": champ, "valeur_fiche": actuelle, "valeur_equipement": attendue})
    return sortie
