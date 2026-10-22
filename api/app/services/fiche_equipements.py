"""Une seule source pour les équipements de la fiche Maison (carnet, lot 7 — point 35).

L'équipement EN SERVICE qui porte `origine_fiche` gagne : les champs correspondants de la
fiche en deviennent une COPIE, écrite par le serveur et verrouillée à la saisie. Le pré-audit
continue de lire la fiche, qui est désormais juste — il n'a pas changé.

Fonctions pures : la route leur passe la maison et ses équipements, et applique le résultat.
Rien n'est inventé : un type sans équivalent dans la fiche laisse le champ LIBRE (le foyer
peut avoir une solution que le carnet ne sait pas nommer), jamais une valeur devinée.

`suggestions_fiche.py` lit la table inverse (`FICHE_VERS_TYPE`) : les deux sens vivent ici.
"""
from datetime import date

# Pour chaque origine : la catégorie d'équipement, le champ « type » de la fiche, et son
# champ « année » (la ventilation et la clim n'en ont pas dans la fiche).
ORIGINES: dict[str, dict] = {
    "chauffage_principal": {"categorie": "chauffage", "type": "chauffage_principal",
                            "annee": "chauffage_principal_annee"},
    "chauffage_appoint": {"categorie": "chauffage", "type": "chauffage_appoint",
                          "annee": "chauffage_appoint_annee"},
    "ecs": {"categorie": "ecs", "type": "ecs", "annee": "ecs_annee"},
    "clim": {"categorie": "clim", "type": None, "annee": None},
    "ventilation": {"categorie": "ventilation", "type": "ventilation", "annee": None},
}

# Type d'équipement → valeurs de fiche ACCEPTÉES, la première étant celle qu'on écrit. Une
# valeur acceptée déjà présente n'est pas réécrite : un réseau de chaleur saisi au carnet
# comme « autre » reste « reseau » dans la fiche (décision du 22/10/2026). Un type absent
# n'a pas d'équivalent : le champ reste libre.
_TYPE_VERS_FICHE: dict[str, dict[str, tuple[str, ...]]] = {
    "chauffage": {
        "PAC_air_eau": ("PAC_air_eau",), "PAC_air_air": ("PAC_air_air",),
        "chaudiere_gaz": ("gaz",), "chaudiere_fioul": ("fioul",),
        "chaudiere_bois": ("bois",), "poele_bois": ("bois",), "poele_granules": ("bois",), "insert": ("bois",),
        "convecteurs": ("elec_direct",), "radiateurs_inertie": ("elec_direct",),
        "autre": ("autre", "reseau"),
    },
    "ecs": {t: (t,) for t in ("ballon_elec", "thermodynamique", "gaz", "solaire", "instantane")},
    "ventilation": {"VMC_simple": ("VMC_simple",), "VMC_double": ("VMC_double",)},
}

# La fiche ne connaît la clim qu'en texte libre : on y écrit le libellé que voit le foyer,
# recopié de `frontend/src/components/carnet/libelles.ts` (à tenir à jour ENSEMBLE).
# « autre » n'a pas de libellé utile : `clim_type` reste libre, seul `clim` est verrouillé.
LIBELLES_CLIM = {"split": "Split", "multisplit": "Multisplit", "gainable": "Gainable",
                 "PAC_air_air": "PAC air/air réversible"}

# Le sens inverse, pour les suggestions du lot 1 : code de fiche → type d'équipement. Ceux
# qui manquent sont repris tels quels (PAC, ballons, VMC : mêmes codes des deux côtés).
FICHE_VERS_TYPE = {
    "elec_direct": "convecteurs", "gaz": "chaudiere_gaz", "fioul": "chaudiere_fioul",
    "bois": "poele_bois", "reseau": "autre",
}

# Pour le message d'un refus : le libellé que le foyer lit dans sa fiche (`FicheMaison.tsx`).
LIBELLES_CHAMPS = {
    "chauffage_principal": "Chauffage principal", "chauffage_principal_annee": "Année d'installation",
    "chauffage_appoint": "Chauffage d'appoint", "chauffage_appoint_annee": "Année d'installation (appoint)",
    "ecs": "Eau chaude sanitaire", "ecs_annee": "Année ECS", "clim": "Climatisation ?",
    "clim_type": "Type de climatisation", "ventilation": "Ventilation",
}


def annee_de(equipement) -> int | None:
    """L'année de pose : celle de la date exacte, sinon l'année seule, sinon rien."""
    if equipement.date_pose:
        return equipement.date_pose.year
    return equipement.annee_pose


def champs_fiche_depuis(equipement, maison=None) -> dict:
    """Les champs de fiche que cet équipement fixe, avec leur valeur. Vide = rien de lié.

    Avec la maison, une valeur de fiche déjà ACCEPTÉE pour ce type est conservée telle
    quelle (« reseau » face à un équipement « autre »). Une année absente de l'équipement
    vide celle de la fiche : la règle est stricte, l'équipement gagne aussi quand il se tait.
    """
    origine = ORIGINES.get(equipement.origine_fiche or "")
    if origine is None or equipement.categorie != origine["categorie"]:
        return {}
    if equipement.origine_fiche == "clim":
        champs = {"clim": True}
        if equipement.type in LIBELLES_CLIM:
            champs["clim_type"] = LIBELLES_CLIM[equipement.type]
        return champs
    acceptees = _TYPE_VERS_FICHE.get(origine["categorie"], {}).get(equipement.type)
    if not acceptees:
        return {}
    actuelle = getattr(maison, origine["type"], None) if maison is not None else None
    champs = {origine["type"]: actuelle if actuelle in acceptees else acceptees[0]}
    if origine["annee"]:
        champs[origine["annee"]] = annee_de(equipement)
    return champs


def champs_a_vider(equipement) -> dict:
    """Mise hors service sans remplaçant (ou suppression) : les champs qu'il fixait, à vide.

    Seuls ceux qu'il VERROUILLAIT : un type sans équivalent n'avait rien écrit, il ne vide rien.
    """
    return {champ: None for champ in champs_fiche_depuis(equipement)}


def _pilotes(equipements) -> list:
    return [e for e in equipements if e.en_service and e.origine_fiche in ORIGINES]


def champs_verrouilles(equipements) -> list[str]:
    """Les champs de fiche qu'un équipement en service fixe : en lecture dans la fiche."""
    verrous: list[str] = []
    for e in _pilotes(equipements):
        verrous += [c for c in champs_fiche_depuis(e) if c not in verrous]
    return verrous


def a_ecrire(maison, equipements) -> dict:
    """Tout ce que les équipements en service imposent à la fiche (valeurs inchangées comprises)."""
    sortie: dict = {}
    for e in _pilotes(equipements):
        sortie.update(champs_fiche_depuis(e, maison))
    return sortie


def ecarts(maison, equipements) -> list[dict]:
    """Les champs où la fiche contredit un équipement en service : ce que la sync corrige."""
    sortie = []
    for e in _pilotes(equipements):
        for champ, valeur in champs_fiche_depuis(e, maison).items():
            ancienne = getattr(maison, champ)
            if ancienne != valeur:
                sortie.append({"champ": champ, "fiche": ancienne, "equipement": valeur,
                               "equipement_id": e.id})
    return sortie


def refus_patch(maison, equipements, champs: dict) -> list[str]:
    """Les champs verrouillés que ce PATCH CHANGERAIT. Renvoyer la même valeur est permis :
    la fiche enregistre un bloc entier (`saveBlock`), champs verrouillés compris."""
    verrous = set(champs_verrouilles(equipements))
    return [c for c, v in champs.items() if c in verrous and getattr(maison, c) != v]


def _decrire(valeur) -> str:
    if valeur is None:
        return "vide"
    if valeur is True:
        return "oui"
    return str(valeur)


def reprise(maison, equipements, aujourd_hui: date) -> dict:
    """Reprise des données existantes (migration 0030), une maison à la fois.

    1. Un équipement sans date face à une fiche datée prend l'année de la fiche — à la
       reprise SEULEMENT : ensuite, l'équipement qui se tait vide la fiche.
    2. Puis l'équipement gagne sur chaque écart restant.
    Chaque geste laisse une entrée de journal. Relancée, elle ne trouve plus rien à faire.
    Met à jour `annee_pose` des objets reçus (la migration passe des copies, pas des modèles).

    Renvoie {"annees": {equipement_id: annee}, "fiche": {champ: valeur}, "journal": [...]}.
    """
    annees, journal = {}, []
    for e in _pilotes(equipements):
        champ_annee = ORIGINES[e.origine_fiche]["annee"]
        if not champ_annee or annee_de(e) is not None or not champs_fiche_depuis(e):
            continue
        annee_fiche = getattr(maison, champ_annee)
        if annee_fiche is not None:
            annees[e.id] = annee_fiche
            e.annee_pose = annee_fiche  # pour que l'étape 2 voie l'équipement daté
            journal.append(_entree(e, aujourd_hui,
                                   f"Année de pose {annee_fiche} reprise de la fiche : l'équipement n'en avait pas."))
    fiche: dict = {}
    par_equipement: dict = {}
    for ec in ecarts(maison, equipements):
        fiche[ec["champ"]] = ec["equipement"]
        par_equipement.setdefault(ec["equipement_id"], []).append(ec)
    for e in _pilotes(equipements):
        if e.id in par_equipement:
            detail = " ; ".join(f"{LIBELLES_CHAMPS[ec['champ']]} : {_decrire(ec['fiche'])}"
                                for ec in par_equipement[e.id])
            journal.append(_entree(e, aujourd_hui, f"Ancienne valeur de la fiche — {detail}."))
    return {"annees": annees, "fiche": fiche, "journal": journal}


def _entree(e, aujourd_hui: date, note: str) -> dict:
    return {"date": aujourd_hui, "type": "autre", "titre": "Fiche mise à jour depuis le carnet",
            "equipement_id": e.id, "note": note}
