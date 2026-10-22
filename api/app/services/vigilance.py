"""La vigilance météo vue d'un foyer (phase 2). Pur.

Sobre par décision : ORANGE et ROUGE seulement, une ligne, une pastille de la couleur de
Météo-France, les gestes de `kb/risques_maison.md` (lus dans la fiche, jamais réécrits) et le
lien vers la carte officielle. Rouge : « Suivez les consignes des autorités ». Après un vent
violent ou des orages : « Noter un dégât » pendant 7 jours.
"""
from datetime import datetime, timedelta
from functools import lru_cache

from app.core.config import settings
from app.services.agents_engine import _REPO_ROOT, parse_faq_markdown
from app.services.meteofrance_vigilance import CARTE_OFFICIELLE

LIBELLES = {"vent": "Vent violent", "orages": "Orages", "pluie_inondation": "Pluie-inondation",
            "canicule": "Canicule", "grand_froid": "Grand froid", "neige_verglas": "Neige-verglas",
            "autre": "Vigilance météo"}
# Intitulés EXACTS de la fiche (testés). Neige-verglas et « autre » n'y ont pas de question.
QUESTIONS = {
    "vent": "Vigilance orange pour vent violent : que faire pour la maison ?",
    "orages": "Vigilance orange pour orages : que faire pour la maison ?",
    "pluie_inondation": "Vigilance orange pour pluie-inondation : que faire pour la maison ?",
    "canicule": "Vigilance canicule : comment protéger la maison et ceux qui y vivent ?",
    "grand_froid": "Vigilance grand froid : que vérifier dans la maison ?",
}
APRES_EPISODE = ("vent", "orages")
AUTORITES = "Suivez les consignes des autorités."


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


@lru_cache(maxsize=1)
def _reponses() -> dict:
    texte = (_REPO_ROOT / "helios" / "kb" / "risques_maison.md").read_text(encoding="utf-8")
    return {e["titre"]: e["content"] for e in parse_faq_markdown(texte)}


def gestes(phenomene: str) -> str | None:
    question = QUESTIONS.get(phenomene)
    if question is None:
        return None
    contenu = _reponses().get(question, "")
    return contenu.split("R:", 1)[-1].strip() if contenu else None


def vigilances_du_foyer(departement: str | None, vigilances, maintenant: datetime) -> list:
    """Les épisodes orange ou rouge du département, en cours ou à venir ; le rouge d'abord."""
    if not departement:
        return []
    actives = [v for v in vigilances if _champ(v, "departement") == departement
               and _champ(v, "couleur") in ("orange", "rouge") and _champ(v, "fin") > maintenant]
    return sorted(actives, key=lambda v: (_champ(v, "couleur") != "rouge", _champ(v, "debut")))


def ligne_a_faire(v, maintenant: datetime) -> dict:
    phen, couleur = _champ(v, "phenomene"), _champ(v, "couleur")
    return {
        "phenomene": phen, "libelle": LIBELLES.get(phen, LIBELLES["autre"]), "couleur": couleur,
        "debut": _champ(v, "debut").isoformat(), "fin": _champ(v, "fin").isoformat(),
        "en_cours": _champ(v, "debut") <= maintenant,
        "question": QUESTIONS.get(phen), "gestes": gestes(phen),
        "autorites": AUTORITES if couleur == "rouge" else None,
        "carte": CARTE_OFFICIELLE,
    }


def apres_episode(departement: str | None, vigilances, maintenant: datetime) -> list[dict]:
    """Vent violent ou orages terminés depuis moins de 7 jours : « Noter un dégât »."""
    if not departement:
        return []
    depuis = maintenant - timedelta(days=settings.vigilance_apres_episode_jours)
    vus, out = set(), []
    for v in sorted(vigilances, key=lambda v: _champ(v, "fin"), reverse=True):
        phen = _champ(v, "phenomene")
        if (_champ(v, "departement") == departement and phen in APRES_EPISODE and phen not in vus
                and depuis <= _champ(v, "fin") <= maintenant):
            vus.add(phen)
            out.append({"phenomene": phen, "libelle": LIBELLES[phen], "fin": _champ(v, "fin").isoformat()})
    return out


def pour_le_chat(actives) -> list[dict] | None:
    """Phénomène, couleur, fin — pour `carnet_contexte` (statut `observe`, source publique)."""
    if not actives:
        return None
    return [{"phenomene": _champ(v, "phenomene"), "couleur": _champ(v, "couleur"),
             "fin": _champ(v, "fin").isoformat()[:16], "statut": "observe"} for v in actives[:3]]
