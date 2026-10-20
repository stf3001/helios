"""La base de connaissances ne doit pas contredire le moteur du pré-audit.

Le pré-audit calcule un temps de retour pour CETTE maison, avec son énergie et son climat :
55 ans pour une PAC air/air dans le Var, quelques années avec du fioul. Une fiche qui promet
un amortissement universel (« en moins de 5 ans ») dit au client le contraire de son propre
audit. Ces formules ont été retirées le 20/10/2026 ; ce test empêche qu'elles reviennent.

On lit TOUS les fichiers de `kb/`, déclarés ou non : le pré-rendu SEO publie tout le dossier.
"""

import pytest

from app.services.agents_engine import _REPO_ROOT, parse_faq_markdown

FICHIERS = sorted(p for p in (_REPO_ROOT / "helios" / "kb").glob("*.md") if p.name != "README.md")
ENTREES = [(p.stem, e) for p in FICHIERS for e in parse_faq_markdown(p.read_text(encoding="utf-8"))]

FORMULES_INTERDITES = (
    "amorti en moins de 5 ans",          # combles : vrai avec du fioul, faux avec une PAC
    "Rentable en 5–8 ans",               # ballon thermodynamique : dépend de son âge
    "forfait au m² qui dépend des revenus",  # combles : plus d'aide par geste depuis le 01/09/2026
)


def test_la_base_est_lue():
    assert len(FICHIERS) > 40 and len(ENTREES) > 400


@pytest.mark.parametrize("formule", FORMULES_INTERDITES)
def test_aucune_entree_ne_promet_une_rentabilite_universelle(formule):
    fautives = [f"{source} : {e['titre']}" for source, e in ENTREES if formule.lower() in e["content"].lower()]
    assert not fautives, f"« {formule} » encore présent dans : {fautives}"


def test_la_section_pour_le_pre_audit_n_est_jamais_ingeree():
    """Les textes courts du lot 4 vivent après le dernier `---` : le parseur doit s'y arrêter."""
    fautives = [f"{source} : {e['titre']}" for source, e in ENTREES if "Pour le pré-audit" in e["content"]]
    assert not fautives, fautives
