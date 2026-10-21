"""Échéances d'entretien du carnet de maison — chargeur et moteur, fonctions pures (lot 3).

DÉTERMINISTE ET SOURCÉ : chaque tâche vient de `api/data/entretien/taches.json`, relue par
Stéphane (`valide_le`), jamais d'un modèle. Le format est décrit dans le `LISEZMOI.md` du
même dossier. Le moteur ne travaille que sur les équipements du carnet (lot 1) et, pour
les tâches de maison, sur les champs de la fiche : il n'invente aucun équipement.

Date de référence d'une échéance, dans cet ordre : dernière fois faite (journal, lot 4),
date de pose, 1er juillet de l'année de pose (SUPPOSÉE), sinon inconnue → « à planifier ».
Sans journal, aucun roulement : une échéance passée reste « en retard », puisque rien ne
dit que l'entretien a été fait.
"""
import json
import logging
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.models.equipement import CATEGORIES, TYPES_PAR_CATEGORIE

logger = logging.getLogger("helios.entretien")

CHEMIN_TABLE = Path(__file__).resolve().parents[2] / "data" / "entretien" / "taches.json"

REGLES = ("mois", "annee_civile")
QUI = ("soi", "pro", "soi_ou_pro")
NATURES = ("obligation", "recommande")
TYPES_SOURCE = ("officiel", "guide", "fabricant", "expertise")
_CHAMPS = {
    "id", "applique_a", "libelle", "regle", "frequence_mois", "n_annees", "puissance_kw", "qui", "nature",
    "mois_preferes", "mois_actifs", "source", "fiche_kb", "valide_le", "note",
}

# Champs de fiche posés aux MAISONS seulement (décision 3 de la table) : pour un appartement,
# ou un logement de type inconnu, leur réponse ne compte pas — ni pour une obligation, ni
# pour une vérification. Avec, pour chacun, la phrase dite quand la réponse est « ne sais pas ».
QUESTIONS_DE_MAISON = {"zone_old": "Vérifiez si votre terrain est concerné"}

# Ordre d'affichage : ce qui presse d'abord ; « à planifier » avant « plus tard », car une
# date inconnue peut cacher un retard.
ORDRE_STATUTS = ("en_retard", "ce_mois", "bientot", "a_planifier", "plus_tard")
JOURS_CE_MOIS = 30
JOURS_BIENTOT = 90


class TacheInvalide(ValueError):
    """Une tâche de la table ne respecte pas le format : le message dit laquelle et pourquoi."""


# ---------------------------------------------------------------------------- chargeur

def _mois(valeur, champ: str) -> None:
    if not (isinstance(valeur, list) and valeur and all(isinstance(m, int) and 1 <= m <= 12 for m in valeur)):
        raise TacheInvalide(f"`{champ}` doit être une liste non vide de mois entre 1 et 12")


def _valider(t: dict, ids_vus: set) -> None:
    if not isinstance(t, dict):
        raise TacheInvalide("une tâche doit être un objet")
    inconnus = set(t) - _CHAMPS
    if inconnus:
        raise TacheInvalide(f"champ(s) inconnu(s) : {', '.join(sorted(inconnus))}")
    if not (isinstance(t.get("id"), str) and t["id"]):
        raise TacheInvalide("`id` manquant")
    if t["id"] in ids_vus:
        raise TacheInvalide("`id` en double")
    if not (isinstance(t.get("libelle"), str) and t["libelle"].strip()):
        raise TacheInvalide("`libelle` manquant")

    applique = t.get("applique_a")
    if not isinstance(applique, dict) or ("maison" in applique) == ("categorie" in applique):
        raise TacheInvalide("`applique_a` doit viser soit une `categorie`, soit la `maison`")
    if "maison" in applique:
        if not isinstance(applique["maison"], dict) or set(applique) != {"maison"}:
            raise TacheInvalide("`applique_a.maison` doit être un objet de conditions (éventuellement vide)")
        if "puissance_kw" in t:
            raise TacheInvalide("`puissance_kw` n'a pas de sens pour une tâche de maison")
    else:
        cats = applique["categorie"]
        cats = [cats] if isinstance(cats, str) else cats
        if not (isinstance(cats, list) and cats and all(c in CATEGORIES for c in cats)):
            raise TacheInvalide(f"`applique_a.categorie` inconnue : {applique['categorie']!r}")
        types = applique.get("types", [])
        connus = {ty for c in cats for ty in TYPES_PAR_CATEGORIE[c]}
        if not isinstance(types, list) or any(ty not in connus for ty in types):
            raise TacheInvalide(f"`applique_a.types` contient un type inconnu pour {cats} : {types!r}")

    regle = t.get("regle", "mois")
    if regle not in REGLES:
        raise TacheInvalide(f"`regle` inconnue : {regle!r}")
    champ_freq = "frequence_mois" if regle == "mois" else "n_annees"
    autre = "n_annees" if regle == "mois" else "frequence_mois"
    if not (isinstance(t.get(champ_freq), int) and t[champ_freq] >= 1):
        raise TacheInvalide(f"la règle `{regle}` exige `{champ_freq}` (entier ≥ 1)")
    if autre in t:
        raise TacheInvalide(f"`{autre}` ne va pas avec la règle `{regle}`")

    if "puissance_kw" in t:
        p = t["puissance_kw"]
        if not (isinstance(p, dict) and set(p) == {"min", "max"}
                and all(isinstance(p[k], (int, float)) for k in p) and p["min"] <= p["max"]):
            raise TacheInvalide("`puissance_kw` doit valoir {\"min\": …, \"max\": …} avec min ≤ max")

    if t.get("qui") not in QUI:
        raise TacheInvalide(f"`qui` inconnu : {t.get('qui')!r}")
    if t.get("nature") not in NATURES:
        raise TacheInvalide(f"`nature` inconnue : {t.get('nature')!r}")
    for champ in ("mois_preferes", "mois_actifs"):
        if champ in t:
            _mois(t[champ], champ)

    source = t.get("source")
    if source is not None:
        if not (isinstance(source, dict) and source.get("type") in TYPES_SOURCE
                and isinstance(source.get("titre"), str) and source["titre"].strip()
                and (source.get("url") is None or isinstance(source.get("url"), str))):
            raise TacheInvalide("`source` doit porter un `type` connu, un `titre` et une `url` (ou null)")
    if t["nature"] == "obligation":
        if source is None or source["type"] != "officiel" or not source.get("url"):
            raise TacheInvalide("une obligation exige une source de type `officiel`, avec titre et URL")

    try:
        date.fromisoformat(t.get("valide_le") or "")
    except (TypeError, ValueError):
        raise TacheInvalide("`valide_le` manquant ou mal écrit : aucune tâche sans relecture de Stéphane") from None


def charger_table(chemin: Path = CHEMIN_TABLE, strict: bool = False) -> dict:
    """La table validée : `version`, `avertissement`, `taches` (les seules tâches valides).

    `strict=True` (tests) : la première tâche invalide lève `TacheInvalide`.
    `strict=False` (production) : elle est ignorée et journalisée, le reste s'affiche.
    """
    brut = json.loads(Path(chemin).read_text(encoding="utf-8"))
    taches, ids = [], set()
    for i, t in enumerate(brut.get("taches", [])):
        try:
            _valider(t, ids)
        except TacheInvalide as exc:
            nom = t.get("id") if isinstance(t, dict) else None
            message = f"tâche n°{i + 1} ({nom or 'sans id'}) : {exc}"
            if strict:
                raise TacheInvalide(message) from None
            logger.warning("Table d'entretien — %s : ignorée", message)
            continue
        ids.add(t["id"])
        taches.append(t)
    return {"version": brut.get("version"), "avertissement": brut.get("avertissement"), "taches": taches}


def charger_taches(chemin: Path = CHEMIN_TABLE, strict: bool = False) -> list[dict]:
    return charger_table(chemin, strict)["taches"]


@lru_cache(maxsize=4)
def _table_en_cache(chemin: str, mtime: float) -> dict:
    return charger_table(Path(chemin))


def table_courante(chemin: Path = CHEMIN_TABLE) -> dict:
    """La table de production, relue seulement quand le fichier change (une alerte par version)."""
    return _table_en_cache(str(chemin), Path(chemin).stat().st_mtime)


# ------------------------------------------------------------------------------ moteur

def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def ajouter_mois(d: date, n: int) -> date:
    """Même jour, n mois plus tard ; ramené au dernier jour du mois s'il n'existe pas (31 → 30)."""
    total = d.month - 1 + n
    annee, mois = d.year + total // 12, total % 12 + 1
    for jour in (d.day, 30, 29, 28):
        try:
            return date(annee, mois, jour)
        except ValueError:
            continue
    raise AssertionError("inatteignable")


def reporter_au_mois_prefere(d: date, mois_preferes: list[int]) -> date:
    """Le 1er du premier mois préféré qui suit `d` ; `d` lui-même s'il tombe déjà dans un mois préféré."""
    if d.month in mois_preferes:
        return d
    for decalage in range(1, 13):
        candidat = ajouter_mois(date(d.year, d.month, 1), decalage)
        if candidat.month in mois_preferes:
            return candidat
    raise AssertionError("inatteignable : mois_preferes est validé non vide")


def statut_echeance(echeance: date | None, aujourd_hui: date) -> str:
    if echeance is None:
        return "a_planifier"
    reste = (echeance - aujourd_hui).days
    if reste < 0:
        return "en_retard"
    if reste <= JOURS_CE_MOIS:
        return "ce_mois"
    return "bientot" if reste <= JOURS_BIENTOT else "plus_tard"


def _reference(tache_id, equipement, derniers_faits) -> tuple[date | None, str]:
    cle = (tache_id, _champ(equipement, "id") if equipement is not None else None)
    if derniers_faits.get(cle):
        return derniers_faits[cle], "journal"
    if equipement is None:
        return None, "inconnue"
    if _champ(equipement, "date_pose"):
        return _champ(equipement, "date_pose"), "date_pose"
    if _champ(equipement, "annee_pose"):
        return date(_champ(equipement, "annee_pose"), 7, 1), "annee_pose"
    return None, "inconnue"


def _echeance(tache: dict, reference: date | None) -> date | None:
    if reference is None:
        return None
    if tache.get("regle", "mois") == "annee_civile":
        # Le texte dit « par année civile » : la limite est le 31 décembre, jamais déplacée.
        return date(reference.year + tache["n_annees"], 12, 31)
    echeance = ajouter_mois(reference, tache["frequence_mois"])
    if tache.get("mois_preferes"):
        echeance = reporter_au_mois_prefere(echeance, tache["mois_preferes"])
    return echeance


def _s_applique(tache: dict, equipement) -> bool:
    applique = tache["applique_a"]
    cats = applique["categorie"]
    cats = [cats] if isinstance(cats, str) else cats
    types = applique.get("types") or []
    return _champ(equipement, "categorie") in cats and (not types or _champ(equipement, "type") in types)


def _puissance(tache: dict, equipement) -> tuple[bool, str | None]:
    """(la tâche vaut-elle pour cet appareil, mention à afficher)."""
    plage = tache.get("puissance_kw")
    if not plage:
        return True, None
    kw = _champ(equipement, "puissance") if _champ(equipement, "unite") == "kW" else None
    if kw is not None:
        return plage["min"] <= kw <= plage["max"], None
    bornes = f"entre {plage['min']:g} et {plage['max']:g} kW"
    if tache["nature"] == "obligation":
        return True, f"Obligatoire si la puissance est {bornes} : vérifiez sur la plaque."
    return True, f"Concerne les appareils {bornes} : vérifiez sur la plaque."


def _maison_concernee(tache: dict, maison) -> bool:
    """Toutes les conditions doivent valoir ; un champ que la fiche n'a pas → non concernée."""
    if maison is None:
        return False
    return all(_condition(maison, champ, attendu) for champ, attendu in tache["applique_a"]["maison"].items())


def _a_le_champ(maison, champ) -> bool:
    return champ in maison if isinstance(maison, dict) else hasattr(maison, champ)


def _condition(maison, champ, attendu) -> bool:
    if not _a_le_champ(maison, champ):
        return False
    if champ in QUESTIONS_DE_MAISON and _champ(maison, "type_logement") != "maison":
        return False
    return _champ(maison, champ) == attendu


def verifications(taches, maison) -> list[dict]:
    """Les tâches de maison qu'on ne peut ni afficher ni écarter : le foyer a répondu « ne sais
    pas » à la question qui en décide. Une ligne sans date, avec le lien de la source pour vérifier.
    """
    if maison is None or _champ(maison, "type_logement") != "maison":
        return []
    lignes = []
    for tache in taches:
        conditions = tache["applique_a"].get("maison")
        if not conditions:
            continue
        inconnues = [c for c in conditions if c in QUESTIONS_DE_MAISON and _champ(maison, c) == "ne_sais_pas"]
        autres_ok = all(_condition(maison, c, v) for c, v in conditions.items() if c not in inconnues)
        if inconnues and autres_ok:
            lignes.append({
                "tache_id": tache["id"],
                "champ": inconnues[0],
                "libelle": QUESTIONS_DE_MAISON[inconnues[0]],
                "tache_libelle": tache["libelle"],
                "nature": tache["nature"],
                "lien": (tache.get("source") or {}).get("url"),
            })
    return lignes


def _ligne(tache, equipement, reference, provenance, aujourd_hui, mention) -> dict:
    echeance = _echeance(tache, reference)
    annee_civile = tache.get("regle", "mois") == "annee_civile"
    return {
        "tache_id": tache["id"],
        "equipement_id": _champ(equipement, "id") if equipement is not None else None,
        "libelle": tache["libelle"],
        "qui": tache["qui"],
        "nature": tache["nature"],
        "source": tache.get("source"),
        "fiche_kb": tache.get("fiche_kb"),
        "note": tache.get("note"),
        "regle": tache.get("regle", "mois"),
        "date_reference": reference,
        "provenance": provenance,
        "reference_supposee": provenance == "annee_pose",
        "echeance": echeance,
        "statut": statut_echeance(echeance, aujourd_hui),
        # Année civile : les mois préférés conseillent une période, ils ne déplacent pas la limite.
        "periode_conseillee": tache.get("mois_preferes") if annee_civile else None,
        "mention_puissance": mention,
    }


def _cle_tri(ligne: dict):
    return (
        ORDRE_STATUTS.index(ligne["statut"]),
        ligne["echeance"] or date.max,
        0 if ligne["nature"] == "obligation" else 1,
        ligne["libelle"],
    )


def echeances(equipements, taches, derniers_faits, aujourd_hui: date, maison=None) -> list[dict]:
    """Une échéance par (équipement en service × tâche qui s'y applique), plus les tâches de maison.

    `derniers_faits` : {(tache_id, equipement_id ou None) : date}, vide tant que le journal
    (lot 4) n'existe pas. Une tâche hors de ses `mois_actifs` n'est pas renvoyée.
    """
    lignes = []
    for tache in taches:
        if tache.get("mois_actifs") and aujourd_hui.month not in tache["mois_actifs"]:
            continue
        if "maison" in tache["applique_a"]:
            if _maison_concernee(tache, maison):
                reference, provenance = _reference(tache["id"], None, derniers_faits)
                lignes.append(_ligne(tache, None, reference, provenance, aujourd_hui, None))
            continue
        for eq in equipements:
            if _champ(eq, "en_service") is False or not _s_applique(tache, eq):
                continue
            vaut, mention = _puissance(tache, eq)
            if not vaut:
                continue
            reference, provenance = _reference(tache["id"], eq, derniers_faits)
            lignes.append(_ligne(tache, eq, reference, provenance, aujourd_hui, mention))
    return sorted(lignes, key=_cle_tri)
