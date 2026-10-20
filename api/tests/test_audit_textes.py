"""Pré-audit v2.4 : un raisonnement qu'on voit.

Les textes affichés viennent des fiches `kb/` (section « Pour le pré-audit »), recopiés mot
pour mot dans `audit_reference.py`. Ces tests tiennent la source unique : si une fiche
change, ils cassent, et le texte se met à jour au même endroit.
"""

import re
from pathlib import Path

import pytest

from app.services import audit_reference as ref
from app.services.audit_engine import run_audit
from tests.test_audit_engine import AUJOURD_HUI, etude, maison_type, reference_complete

KB = Path(__file__).resolve().parents[2] / "kb"


def _section_preaudit(fiche: str) -> str:
    texte = (KB / f"{fiche}.md").read_text(encoding="utf-8")
    assert "## Pour le pré-audit" in texte, fiche
    return texte.split("## Pour le pré-audit", 1)[1]


def _items(section: str, cle: str) -> list[str]:
    """Les éléments « a · b · c » d'une ligne `- **cle** : …` de la section."""
    m = re.search(rf"^- \*\*{cle}\*\* : (.*)$", section, re.M)
    assert m, cle
    return [x.strip() for x in m.group(1).split("·")]


def _phrase(section: str, cle: str) -> str:
    m = re.search(rf"^- \*\*{cle}\*\* : « (.*) »$", section, re.M)
    assert m, cle
    return m.group(1)


@pytest.mark.parametrize("action", sorted(ref.TEXTES_ACTIONS))
def test_les_textes_des_actions_sont_ceux_de_la_fiche(action):
    t = ref.TEXTES_ACTIONS[action]
    section = _section_preaudit(t["fiche"])
    for cle, valeur in t.items():
        if cle in ("fiche", "question"):
            continue
        if isinstance(valeur, tuple):
            assert list(valeur) == _items(section, cle), (action, cle)
        else:
            assert valeur == _phrase(section, cle), (action, cle)
    # La question mène à la page de la fiche dans la FAQ : elle doit exister telle quelle.
    assert f"### Q: {t['question']}\n" in (KB / f"{t['fiche']}.md").read_text(encoding="utf-8")


# --- Maison de référence --------------------------------------------------------------------

@pytest.fixture
def ref_audit():
    return run_audit(reference_complete(), aujourd_hui=AUJOURD_HUI)


def _action(r: dict, cle: str) -> dict:
    return next(a for a in r["priorites"] if a["action"] == cle)


def test_les_combles_expliquent_leur_classement(ref_audit):
    combles = _action(ref_audit, "isolation_combles")
    assert combles["horizon"] == "a_l_occasion"
    assert combles["pourquoi"].startswith("Votre toit perd beaucoup de chaleur")
    assert "une pompe à chaleur air/air" in combles["pourquoi"]
    assert "doux (H3)" in combles["pourquoi"]
    assert combles["benefices"] and combles["vigilance"] and combles["devis"]
    assert combles["fiche"] == "action_combles"


def test_le_ballon_dit_son_age(ref_audit):
    ballon = _action(ref_audit, "ballon_thermodynamique")
    assert ballon["pourquoi"].startswith("Votre ballon a 16 ans")
    assert "Avec des panneaux" not in ballon["pourquoi"]  # pas d'étude du simulateur


def test_avec_une_etude_le_ballon_parle_des_panneaux():
    r = run_audit(reference_complete(), etude_simulateur=etude(), aujourd_hui=AUJOURD_HUI)
    assert "Avec des panneaux" in _action(r, "ballon_thermodynamique")["pourquoi"]


def test_un_ballon_recent_n_est_pas_au_remplacement():
    r = run_audit(reference_complete(ecs_annee=2022), aujourd_hui=AUJOURD_HUI)
    assert _action(r, "ballon_thermodynamique")["pourquoi"].startswith("Votre ballon fonctionne")


@pytest.mark.parametrize("house", [reference_complete(), maison_type(), maison_type(chauffage_principal="gaz"),
                                   maison_type(chauffage_principal="elec_direct")])
def test_aucune_variable_non_remplie(house):
    r = run_audit(house, etude_simulateur=etude(), aujourd_hui=AUJOURD_HUI)
    assert not re.search(r"\{[a-z_]+\}", repr(r))


def test_le_fioul_dit_que_sa_chaleur_coute_cher():
    r = run_audit(maison_type(), aujourd_hui=AUJOURD_HUI)
    combles = _action(r, "isolation_combles")
    assert combles["horizon"] == "prioritaire"
    assert combles["pourquoi"].startswith("Avec une chaudière fioul, chaque kWh perdu")


def test_convecteurs_et_pac_air_eau_la_note_du_circuit_d_eau():
    pac = _action(run_audit(maison_type(chauffage_principal="elec_direct"), aujourd_hui=AUJOURD_HUI), "pac_air_eau")
    assert "pas de circuit d'eau" in pac["pourquoi"]
