"""Les projets de la maison (carnet, lot 9) — modèles, visibilité, recopie d'une étude. Pur.

Un projet va de l'idée à la réception des travaux. Il ne CALCULE rien : son budget et son
économie viennent d'un calcul déjà fait — étude du simulateur, pré-audit — recopiés tels
quels avec leur date et leur statut, ou d'un devis saisi par le foyer (`declare`). Sans
calcul, l'écran renvoie vers l'outil.

Aucun texte d'explication ici : chaque modèle renvoie à des fiches `kb/` par leur
identifiant de source. Un modèle dont une fiche n'existe pas n'est pas servi.
Le format de `api/data/projets/modeles.json` est décrit dans le `LISEZMOI.md` du dossier.
"""
import json
from datetime import datetime
from pathlib import Path

from app.models.equipement import ORIGINES_FICHE, TYPES_PAR_CATEGORIE
from app.models.travaux import CATEGORIES_CIL
from app.services.audit_reference import ACTIONS

CHEMIN_MODELES = Path(__file__).resolve().parents[2] / "data" / "projets" / "modeles.json"

ETAPES = ("idee", "etude", "devis", "decide", "travaux", "termine", "abandonne")
# Ce que le foyer peut choisir lui-même : `termine` passe par « Les travaux sont terminés »,
# qui crée travaux, garanties, équipements et journal.
ETAPES_LIBRES = tuple(e for e in ETAPES if e != "termine")
FAMILLES = ("solaire_stockage", "sortie_fossile", "ecosysteme", "enveloppe")
# Plus « pre-audit:<clé d'action> ». `aucun` : pas de calculateur (point 51) — l'écran renvoie aux
# fiches. L'outil `eau` a été retiré avec le potentiel hydrique (point 13).
OUTILS = ("simulateur-solaire", "vent", "jardin", "aucun")
POSTES_SIMULATEUR = ("panneaux_eur", "carport_eur", "batterie_eur", "inertie_eur", "eolien_eur")
CHAMPS_MASQUE = ("statut", "type_logement", "chauffage_principal")
MAX_PROJETS_PAR_MAISON = 20
# Pour un modèle `mention_locataire` (la régulation, souvent un thermostat) que voit un locataire.
MENTION_LOCATAIRE = "Les travaux sur le chauffage se décident avec votre propriétaire."

_CHAMPS = {"id", "titre", "famille", "outil", "poste", "fiches_kb", "equipements_crees", "lourd",
           "masque_si", "affiche_si", "categorie_cil", "mention_locataire"}


class ModeleInvalide(ValueError):
    """Un modèle ne respecte pas le format : le message dit lequel et pourquoi."""


def _valider(m: dict, ids: set) -> None:
    if set(m) - _CHAMPS:
        raise ModeleInvalide(f"champ(s) inconnu(s) : {', '.join(sorted(set(m) - _CHAMPS))}")
    if not (isinstance(m.get("id"), str) and m["id"]) or m["id"] in ids:
        raise ModeleInvalide("`id` manquant ou en double")
    if not (isinstance(m.get("titre"), str) and m["titre"].strip()):
        raise ModeleInvalide("`titre` manquant")
    if m.get("famille") not in FAMILLES:
        raise ModeleInvalide(f"`famille` inconnue : {m.get('famille')!r}")
    outil = m.get("outil")
    if not (outil in OUTILS or (isinstance(outil, str) and outil.startswith("pre-audit:") and len(outil) > 10)):
        raise ModeleInvalide(f"`outil` inconnu : {outil!r}")
    if outil.startswith("pre-audit:") and outil.split(":", 1)[1] not in ACTIONS:
        raise ModeleInvalide(f"action du pré-audit inconnue : {outil!r}")
    if outil == "simulateur-solaire" and m.get("poste") not in POSTES_SIMULATEUR:
        raise ModeleInvalide("un modèle du simulateur dit quel `poste` de l'investissement le concerne")
    if not (isinstance(m.get("fiches_kb"), list) and m["fiches_kb"]):
        raise ModeleInvalide("`fiches_kb` doit nommer au moins une fiche")
    for e in m.get("equipements_crees", []):
        if TYPES_PAR_CATEGORIE.get(e.get("categorie"), ()) and e.get("type") in TYPES_PAR_CATEGORIE[e["categorie"]]:
            if e.get("origine_fiche") not in (None, *ORIGINES_FICHE):
                raise ModeleInvalide(f"`origine_fiche` inconnue : {e['origine_fiche']!r}")
            continue
        raise ModeleInvalide(f"équipement inconnu : {e!r}")
    for cle in ("masque_si", "affiche_si"):
        cond = m.get(cle, {})
        if not isinstance(cond, dict) or any(c not in CHAMPS_MASQUE or not isinstance(v, list) for c, v in cond.items()):
            raise ModeleInvalide(f"`{cle}` : {{champ de fiche : [valeurs]}} attendu")
    if not isinstance(m.get("lourd"), bool):
        raise ModeleInvalide("`lourd` (vrai ou faux) est obligatoire")
    if m.get("categorie_cil") not in (None, *CATEGORIES_CIL):
        raise ModeleInvalide(f"`categorie_cil` inconnue : {m['categorie_cil']!r}")
    if not isinstance(m.get("mention_locataire", False), bool):
        raise ModeleInvalide("`mention_locataire` : vrai ou faux")


def charger_modeles(chemin: Path = CHEMIN_MODELES) -> list[dict]:
    """Stricte : un fichier de modèles se corrige avant de partir, il ne se dégrade pas."""
    brut = json.loads(Path(chemin).read_text(encoding="utf-8"))
    modeles, ids = [], set()
    for i, m in enumerate(brut.get("modeles", [])):
        try:
            _valider(m, ids)
        except ModeleInvalide as exc:
            raise ModeleInvalide(f"modèle n°{i + 1} ({m.get('id', 'sans id')}) : {exc}") from None
        ids.add(m["id"])
        modeles.append(m)
    return modeles


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def mention(modele: dict, parcours: dict) -> str | None:
    """La mention d'un modèle léger que voit un locataire, sinon rien."""
    return MENTION_LOCATAIRE if modele.get("mention_locataire") and parcours.get("profil") == "locataire" else None


def fiches_manquantes(modele: dict, sources: set[str]) -> list[str]:
    return [f for f in modele["fiches_kb"] if f not in sources]


def modeles_visibles(modeles: list[dict], maison, parcours: dict, sources: set[str]) -> list[dict]:
    """Ce que ce foyer peut envisager. Écartés : un modèle dont une fiche manque, un projet
    lourd pour qui ne voit pas les projets lourds (locataire), un `masque_si` qui vaut, un
    `affiche_si` contredit par la fiche (un champ NON renseigné ne cache rien)."""
    sortie = []
    for m in modeles:
        if fiches_manquantes(m, sources):
            continue
        if m["lourd"] and not parcours.get("voit_projets_lourds", True):
            continue
        if any(_champ(maison, c) in v for c, v in m.get("masque_si", {}).items()):
            continue
        if any(_champ(maison, c) is not None and _champ(maison, c) not in v for c, v in m.get("affiche_si", {}).items()):
            continue
        sortie.append(m)
    return sortie


# ------------------------------------------------------------- recopie d'une étude

def _jour(d) -> str:
    return (d.date() if isinstance(d, datetime) else d).isoformat()


def depuis_simulateur(resultat: dict, poste: str, cree_le, etude_id) -> dict | None:
    """Une étude du simulateur qui contient ce poste : son coût et son économie, TELS QUELS.

    L'économie de l'étude porte sur toute la configuration : quand elle compte d'autres
    postes que celui du projet, le périmètre le dit (`ensemble`) au lieu de la lui attribuer.
    """
    invest = resultat.get("investissement") or {}
    if not invest.get(poste):
        return None
    autres = [p for p in POSTES_SIMULATEUR if p != poste and invest.get(p)]
    eco = (resultat.get("indicateurs") or {}).get("economie_1re_annee_eur")
    return {
        "etude_ref": {"type": "simulateur", "id": str(etude_id), "date": _jour(cree_le),
                      "perimetre_economie": "ensemble" if autres else "projet", "autres_postes": autres},
        "budget_bas_eur": invest[poste], "budget_haut_eur": invest[poste],
        "budget_source": "etude", "budget_statut": "suppose", "budget_date": _jour(cree_le),
        "economie_annuelle_eur": eco, "economie_source": "etude" if eco is not None else None,
        "economie_statut": "calcule" if eco is not None else None,
        "economie_date": _jour(cree_le) if eco is not None else None,
    }


def action_d_audit(json_result: dict, cle: str) -> dict | None:
    for p in (json_result or {}).get("priorites") or []:
        if isinstance(p, dict) and p.get("action") == cle and isinstance(p.get("cout_eur"), dict):
            return p
    return None


def depuis_audit(json_result: dict, cle: str, cree_le, audit_id) -> dict | None:
    """Le chiffrage d'une action du pré-audit (formats v2 et suivants), recopié tel quel :
    coût bas et haut, économie centrale, et les statuts que le moteur leur a donnés."""
    p = action_d_audit(json_result, cle)
    if p is None:
        return None
    statuts = p.get("statuts") or {}
    eco = (p.get("economie_annuelle_eur") or {}).get("central")
    return {
        "etude_ref": {"type": "audit", "id": str(audit_id), "date": _jour(cree_le), "action": cle},
        "budget_bas_eur": p["cout_eur"].get("bas"), "budget_haut_eur": p["cout_eur"].get("haut"),
        "budget_source": "audit", "budget_statut": statuts.get("cout_eur") or "suppose",
        "budget_date": _jour(cree_le),
        "economie_annuelle_eur": eco, "economie_source": "audit" if eco is not None else None,
        "economie_statut": (statuts.get("economie_annuelle_eur") or "calcule") if eco is not None else None,
        "economie_date": _jour(cree_le) if eco is not None else None,
    }


def equipements_a_creer(modele: dict, confirmes: list[int]) -> list[dict]:
    """Les propositions du modèle que le foyer a cochées (par leur rang), rien de plus."""
    proposes = modele.get("equipements_crees", [])
    if any(not isinstance(i, int) or not 0 <= i < len(proposes) for i in confirmes):
        raise ValueError("Équipement proposé inconnu")
    return [proposes[i] for i in sorted(set(confirmes))]
