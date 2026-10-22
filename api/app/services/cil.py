"""« À compléter pour votre carnet d'information du logement » (carnet, lot 11) — pur.

Un INDICATEUR, sans valeur légale : pour chaque chantier d'une catégorie du carnet
d'information du logement (CIL), réceptionné depuis le 01/01/2023, ce que le carnet d'Hélios
ne sait pas encore. Rien n'est obligatoire : on montre ce qui manque, chaque manque relié au
formulaire qui le complète (`objet` + `id`).

Rubriques d'après le code de la construction et de l'habitation (art. L. 126-35-2 et
suivants, R. 126-32 à R. 126-34) et l'arrêté du 27 décembre 2022 (articles 2 à 6 : toitures,
murs, parois vitrées et portes, planchers bas, chauffage-refroidissement-eau chaude).
"""
from datetime import date

DEBUT_CIL = date(2023, 1, 1)
CATEGORIES_ISOLATION = ("isolation_toiture", "isolation_murs", "planchers_bas")
# Équipements du chantier « chauffage, refroidissement, eau chaude » (arrêté, art. 6).
CATEGORIES_EQUIPEMENT = ("chauffage", "ecs", "clim")
# Appareils dont l'entretien donne une attestation : combustion et systèmes thermodynamiques.
TYPES_ATTESTES = ("chaudiere_gaz", "chaudiere_fioul", "chaudiere_bois", "poele_bois", "poele_granules", "insert",
                  "PAC_air_eau", "PAC_air_air", "thermodynamique", "split", "multisplit", "gainable")

CHAMPS_ISOLANT = ("nature", "marque_reference", "resistance_thermique", "conductivite", "epaisseur_mm",
                  "surface_m2", "interfaces")
CHAMPS_EQUIPEMENT = ("marque", "modele", "numero_serie", "puissance", "mode_evacuation", "etiquette_energie")
# Une réponse « je ne sais pas » laisse le manque ouvert : c'est une information à retrouver.
_INCONNUES = {"mode_evacuation": "inconnu", "etiquette_energie": "inconnue"}


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _vide(obj, champ) -> bool:
    v = _champ(obj, champ)
    return v is None or (isinstance(v, str) and not v.strip()) or v == _INCONNUES.get(champ)


def concerne(t) -> bool:
    reception = _champ(t, "date_reception")
    return (_champ(t, "categorie_cil") not in (None, "autre")
            and reception is not None and reception >= DEBUT_CIL)


def a_completer(travaux, equipements, isolants, journal) -> list[dict]:
    """Un bloc par chantier concerné : `manques` vide = rien à compléter."""
    sortie = []
    for t in travaux:
        if not concerne(t):
            continue
        tid, cat = _champ(t, "id"), _champ(t, "categorie_cil")
        manques = []
        if _vide(t, "note"):
            manques.append({"objet": "travaux", "id": tid, "champs": ["description"]})
        if cat in CATEGORIES_ISOLATION:
            siens = [i for i in isolants if _champ(i, "travaux_id") == tid]
            if not siens:
                manques.append({"objet": "travaux", "id": tid, "champs": ["isolant"]})
            for i in siens:
                champs = [c for c in CHAMPS_ISOLANT if _vide(i, c)]
                if champs:
                    manques.append({"objet": "isolant", "id": _champ(i, "id"), "champs": champs})
        if cat == "chauffage_froid_ecs":
            siens = [e for e in equipements
                     if _champ(e, "travaux_id") == tid and _champ(e, "categorie") in CATEGORIES_EQUIPEMENT]
            if not siens:
                manques.append({"objet": "travaux", "id": tid, "champs": ["equipement"]})
            for e in siens:
                champs = [c for c in CHAMPS_EQUIPEMENT if _vide(e, c)]
                if champs:
                    manques.append({"objet": "equipement", "id": _champ(e, "id"), "champs": champs})
                if _champ(e, "type") in TYPES_ATTESTES:
                    # Un entretien noté sans document : l'attestation est à joindre.
                    for j in journal:
                        if (_champ(j, "equipement_id") == _champ(e, "id")
                                and _champ(j, "type") in ("entretien", "controle")
                                and _champ(j, "document_id") is None):
                            manques.append({"objet": "journal", "id": _champ(j, "id"), "champs": ["attestation"]})
        sortie.append({"travaux_id": tid, "nature": _champ(t, "nature"), "categorie_cil": cat,
                       "date_reception": _champ(t, "date_reception"), "manques": manques})
    return sortie
