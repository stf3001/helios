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


# --- Étape 2 : les gestes par équipement ----------------------------------------------------

def test_les_gestes_de_fiche_sont_ceux_de_la_fiche():
    section = _section_preaudit("gestes_equipements")
    gestes = [g for g in ref.GESTES_GRATUITS if g.get("fiche")]
    assert {g["cle"] for g in gestes} == {"pac_air_air", "clim", "ballon_elec", "ballon_thermo", "eau_chaude_tous"}
    for g in gestes:
        assert g["texte"] == _phrase(section, g["cle"]), g["cle"]
    assert ref.CONFORT_ETE_CLIM_EXISTANTE == _phrase(section, "confort_ete_clim_existante")


def test_reference_gestes_propres_aux_equipements(ref_audit):
    cles = [g["cle"] for g in ref_audit["gestes"]]
    assert {"pac_air_air", "clim", "ballon_elec", "eau_chaude_tous"} <= set(cles)
    assert len(cles) <= ref.GESTES_MAX
    # Le geste de la fiche remplace ceux qui disaient la même chose : pas de doublon.
    assert not {"consigne_19", "programmation", "filtres_pac"} & set(cles)
    assert ref_audit["confort_ete"]["note_clim"] == ref.CONFORT_ETE_CLIM_EXISTANTE


def test_gestes_d_une_maison_au_gaz_sans_clim():
    r = run_audit(maison_type(chauffage_principal="gaz", ecs="thermodynamique"), aujourd_hui=AUJOURD_HUI)
    cles = [g["cle"] for g in r["gestes"]]
    assert cles[:3] == ["consigne_19", "programmation", "entretien_chaudiere"]
    assert "ballon_thermo" in cles and "clim" not in cles and "ballon_elec" not in cles
    assert len(cles) <= ref.GESTES_MAX
    assert r["confort_ete"]["note_clim"] is None


# --- Étape 3 : les leviers du contrat --------------------------------------------------------

def test_les_leviers_sont_ceux_de_la_fiche():
    section = _section_preaudit(ref.FICHE_CONTRAT)
    for cle, texte in ref.LEVIERS_CONTRAT.items():
        assert texte == _phrase(section, cle), cle


def _leviers(**kw) -> set[str]:
    return {x["cle"] for x in run_audit(reference_complete(**kw), aujourd_hui=AUJOURD_HUI)["contrat"]}


def test_aucun_levier_sans_le_champ_renseigne(ref_audit):
    assert ref_audit["contrat"] == []  # ni puissance, ni option, ni prix bloqué dans la fiche


@pytest.mark.parametrize("kw, attendu", [
    ({"puissance_souscrite": "12"}, True),    # PAC : 9 kVA habituels
    ({"puissance_souscrite": "9"}, False),
])
def test_puissance_a_verifier(kw, attendu):
    assert ("puissance_a_verifier" in _leviers(**kw)) is attendu


def test_puissance_habituelle_plus_basse_sans_chauffage_electrique():
    r = run_audit(maison_type(puissance_souscrite="9"), aujourd_hui=AUJOURD_HUI)  # fioul : 6 kVA
    levier = next(x for x in r["contrat"] if x["cle"] == "puissance_a_verifier")
    assert levier["texte"].startswith("Votre abonnement est de 9 kVA.")


def test_heures_creuses_et_base_avec_ballon():
    assert "hphc_ballon" in _leviers(option_tarifaire="HPHC")
    assert "hphc_ballon" not in _leviers(option_tarifaire="HPHC", ecs="thermodynamique")
    assert "base_avec_ballon" in _leviers(option_tarifaire="base")
    assert not {"hphc_ballon", "base_avec_ballon"} & _leviers(option_tarifaire="tempo")
    avec_etude = run_audit(reference_complete(option_tarifaire="base"), etude_simulateur=etude(),
                           aujourd_hui=AUJOURD_HUI)
    assert avec_etude["contrat"] == []


@pytest.mark.parametrize("kw, attendu", [
    ({"tarif_bloque": "oui", "tarif_bloque_mois_restants": 2}, True),
    ({"tarif_bloque": "oui", "tarif_bloque_mois_restants": 3}, True),
    ({"tarif_bloque": "oui", "tarif_bloque_mois_restants": 4}, False),
    ({"tarif_bloque": "oui"}, False),
    ({"tarif_bloque": "non", "tarif_bloque_mois_restants": 2}, False),
])
def test_fin_du_prix_bloque(kw, attendu):
    assert ("tarif_bloque_fin" in _leviers(**kw)) is attendu


def test_le_prix_bloque_cite_ses_mois():
    r = run_audit(reference_complete(tarif_bloque="oui", tarif_bloque_mois_restants=2), aujourd_hui=AUJOURD_HUI)
    assert r["contrat"][0]["texte"].startswith("Votre prix bloqué se termine dans 2 mois")


# --- Étape 4 : les conseils de parcours ------------------------------------------------------

def test_les_textes_de_parcours_sont_ceux_des_fiches():
    assert ref.DPE_ELECTRIQUE_2026 == _phrase(_section_preaudit(ref.FICHE_DPE), "dpe_electrique_2026")
    section = _section_preaudit(ref.FICHE_AMPLEUR)
    assert ref.PISTE_AMPLEUR == _phrase(section, "piste_ampleur")
    assert list(ref.VIGILANCE_AMPLEUR) == _items(section, "vigilance")
    corps = (KB / f"{ref.FICHE_AMPLEUR}.md").read_text(encoding="utf-8").replace("**", "")
    assert ref.FOSSILE_AMPLEUR in corps


def test_dpe_electrique_d_avant_2026():
    r = run_audit(reference_complete(dpe_annee=2024), aujourd_hui=AUJOURD_HUI)
    assert r["dpe_attestation"]["texte"] == ref.DPE_ELECTRIQUE_2026
    assert not re.search(r"\b[A-G]\b", r["dpe_attestation"]["texte"])  # jamais de lettre estimée
    assert run_audit(reference_complete(dpe_annee=2026), aujourd_hui=AUJOURD_HUI)["dpe_attestation"] is None
    assert run_audit(reference_complete(dpe_annee=2024, chauffage_principal="gaz"),
                     aujourd_hui=AUJOURD_HUI)["dpe_attestation"] is None
    assert run_audit(reference_complete(), aujourd_hui=AUJOURD_HUI)["dpe_attestation"] is None  # année inconnue


def test_maison_f_au_fioul_mal_isolee_voit_la_renovation_d_ampleur():
    r = run_audit(maison_type(type_logement="maison", dpe_lettre="F"), aujourd_hui=AUJOURD_HUI)
    amp = r["renovation_ampleur"]
    assert amp["texte"].startswith("Votre maison est classée F")
    assert amp["fossile"] == ref.FOSSILE_AMPLEUR
    assert not re.search(r"\d", amp["texte"].replace("France Rénov'", ""))  # aucun chiffre


@pytest.mark.parametrize("kw", [
    {"type_logement": "appartement", "dpe_lettre": "F"},
    {"type_logement": "maison", "dpe_lettre": "D"},
    {"type_logement": "maison", "dpe_lettre": "F", "statut": "locataire"},
    {"type_logement": "maison", "dpe_lettre": "F", "isolation_murs": "bonne", "menuiseries": "double"},
])
def test_pas_de_piste_d_ampleur_hors_cible(kw):
    assert run_audit(maison_type(**kw), aujourd_hui=AUJOURD_HUI)["renovation_ampleur"] is None


def test_ampleur_sans_chaudiere_fossile_pas_de_phrase_fossile():
    r = run_audit(maison_type(type_logement="maison", dpe_lettre="G", chauffage_principal="elec_direct"),
                  aujourd_hui=AUJOURD_HUI)
    assert r["renovation_ampleur"]["fossile"] is None
