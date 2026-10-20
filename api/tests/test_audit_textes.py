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


def test_convecteurs_la_pac_air_air_porte_la_note_du_circuit_d_eau():
    pac = _action(run_audit(maison_type(chauffage_principal="elec_direct"), aujourd_hui=AUJOURD_HUI), "pac_air_air")
    assert pac["contexte"] == ref.TEXTES_ACTIONS["pac_air_air"]["note_convecteurs"]
    assert "pas de circuit d'eau" not in (pac["pourquoi"] or "")  # dite une fois, en contexte
    assert pac["benefices"] == list(ref.TEXTES_ACTIONS["pac_air_air"]["benefices_convecteurs"])
    assert pac["devis"] == list(ref.TEXTES_ACTIONS["pac_air_air"]["devis_convecteurs"])


@pytest.mark.parametrize("surface, unites", [(20, 1), (100, 4), (300, 6), (None, 1)])
def test_nombre_d_unites_borne(surface, unites):
    r = run_audit(maison_type(chauffage_principal="elec_direct", surface_habitable=surface), aujourd_hui=AUJOURD_HUI)
    assert _action(r, "pac_air_air")["quantite"]["valeur"] == unites


@pytest.mark.parametrize("chauffage", ["gaz", "fioul"])
def test_le_fossile_garde_la_pac_air_eau(chauffage):
    actions = {a["action"] for a in run_audit(maison_type(chauffage_principal=chauffage),
                                              aujourd_hui=AUJOURD_HUI)["priorites"]}
    assert "pac_air_eau" in actions and "pac_air_air" not in actions


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


# --- Étape 5 : la PAC air/air au remplacement ------------------------------------------------

def test_la_pac_de_16_ans_chiffre_son_remplacement(ref_audit):
    """2 100 kWh × (1 − 3,0 / 4,3) × 0,2001 € = 127 €/an, ±15 % : 108 à 146 €."""
    pac = next(x for x in ref_audit["conseils_equipements"] if x["equipement"] == "PAC_air_air")
    eco = pac["economie_au_remplacement_eur"]
    assert eco == {"bas": 108, "haut": 146}
    assert 0 < eco["bas"] <= eco["haut"] <= ref_audit["consommation"]["cout_chauffage_actuel_eur"]
    assert "d'environ 108 à 146 €/an" in pac["texte"]
    assert pac["statut"] == "calcule"
    assert "cout_eur" not in pac and "temps_retour_ans" not in pac  # un conseil, pas une action
    assert "scop_pac_air_air_neuf" in {h["cle"] for h in ref_audit["hypotheses"]}
    # Hors synthèse : le plan recommandé reste le seul ballon.
    assert ref_audit["synthese"]["plan_recommande"]["nb"] == 1


def test_le_ballon_n_a_pas_d_economie_au_remplacement(ref_audit):
    ballon = next(x for x in ref_audit["conseils_equipements"] if x["equipement"] == "ballon_elec")
    assert "economie_au_remplacement_eur" not in ballon


# --- Étapes 7 et 8 : le climat et le coût dans le temps --------------------------------------

def test_reference_climat(ref_audit):
    """Chauffage : 2 100 kWh × 0,079 = 166 kg → 170. Eau chaude : 4 × 800 = 3 200 kWh × 0,065
    = 208 → 210. Après le ballon (− 2 080 kWh) : 166 + 1 120 × 0,065 = 239 → 240."""
    cl = ref_audit["climat"]
    assert cl["chauffage_kg_an"] == 170
    assert cl["eau_chaude_kg_an"] == 210
    assert cl["apres_plan_recommande_kg_an"] == 240
    assert cl["apres_plan_recommande_kg_an"] <= cl["chauffage_kg_an"] + cl["eau_chaude_kg_an"]
    assert cl["apres_tout_le_plan_kg_an"] <= cl["apres_plan_recommande_kg_an"]
    assert cl["statut"] == "calcule"
    assert "facteurs_co2_kg_kwh" in {h["cle"] for h in ref_audit["hypotheses"]}


def test_le_fioul_vers_la_pac_compte_l_electricite_ajoutee():
    r = run_audit(maison_type(), aujourd_hui=AUJOURD_HUI)
    cl = r["climat"]
    assert cl["chauffage_kg_an"] == round(11647.06 * 0.324, -1)
    assert cl["apres_tout_le_plan_kg_an"] < cl["apres_plan_recommande_kg_an"] < cl["chauffage_kg_an"]
    pac = _action(r, "pac_air_eau")
    # Après la PAC, le chauffage restant est de l'électricité, au facteur de l'électricité.
    assert cl["apres_tout_le_plan_kg_an"] >= round(pac["conso_apres_kwh_electricite"] * 0.079 * 0.5, -1)


def test_eau_chaude_au_gaz_inconnue():
    r = run_audit(maison_type(chauffage_principal="gaz", ecs="gaz"), aujourd_hui=AUJOURD_HUI)
    assert r["climat"]["eau_chaude_kg_an"] is None
    assert r["couts"]["eau_chaude_eur_an"] is None


def test_reference_couts_sur_10_ans(ref_audit):
    """Eau chaude : 3 200 kWh × 0,2001 = 640 €/an. 10 ans à +2 %/an : × 10,95."""
    co = ref_audit["couts"]
    assert co["chauffage_eur_an"] == 420 and co["eau_chaude_eur_an"] == 640
    assert co["hausse_pct_an"] == 2.0
    assert co["chauffage_et_eau_chaude_10_ans_eur"] > 10 * (co["chauffage_eur_an"] + co["eau_chaude_eur_an"])
    facteur = sum(1.02 ** an for an in range(10))
    assert co["chauffage_et_eau_chaude_10_ans_eur"] == round(1060 * facteur, -1)
    eco = ref_audit["synthese"]["plan_recommande"]["economie_annuelle_eur"]["central"]
    assert co["economie_10_ans_plan_recommande_eur"] == round(eco * facteur, -1)
    assert "hausse_prix_pct_an" in {h["cle"] for h in ref_audit["hypotheses"]}


# --- Étape 9 : le chat et le PDF -------------------------------------------------------------

from datetime import datetime  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from app.services import pdf_audit  # noqa: E402
from app.services.rag import CONSIGNE_AUDIT_PRIME, build_audit_context  # noqa: E402


def test_le_chat_recoit_le_raisonnement(ref_audit):
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 20), json_result=ref_audit))
    assert next(iter(ctx)) == "consigne_prioritaire" and ctx["consigne_prioritaire"] == CONSIGNE_AUDIT_PRIME
    combles = next(a for a in ctx["priorites"] if a["label"].startswith("Isolation des combles"))
    assert combles["pourquoi"] and combles["vigilance"]
    assert ctx["economie_remplacement_pac"] == {"bas": 108, "haut": 146}
    assert ctx["climat"]["chauffage_kg_an"] == 170 and ctx["couts"]["hausse_pct_an"] == 2.0
    assert ctx["contrat"] is None and ctx["dpe_attestation"] is None


@pytest.fixture
def pdf_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_audit, "PDF_DIR", tmp_path)


def _pages(audit: dict) -> list[str]:
    from pypdf import PdfReader
    chemin = pdf_audit.build_pdf(audit, house_label="Maison · 83000")
    return [p.extract_text().replace(" ", " ") for p in PdfReader(chemin).pages]


@pytest.mark.parametrize("house", [reference_complete(), maison_type(),
                                   maison_type(type_logement="maison", dpe_lettre="F", puissance_souscrite="9",
                                               option_tarifaire="HPHC", ecs="ballon_elec")],
                         ids=["reference", "fioul", "fioul_F"])
def test_le_pdf_explique(pdf_tmp, house):
    pages = _pages(run_audit(house, aujourd_hui=AUJOURD_HUI))
    texte = " ".join(pages)
    assert len(pages) <= 5
    for attendu in ("Pourquoi", "À surveiller", "Ce que ça apporte", "kg/an", "Sur 10 ans"):
        assert attendu in texte, attendu
    assert not re.search(r"\{[a-z_]+\}", texte)


def test_le_pdf_du_fioul_f_porte_contrat_et_ampleur(pdf_tmp):
    house = maison_type(type_logement="maison", dpe_lettre="F", puissance_souscrite="9",
                        option_tarifaire="HPHC", ecs="ballon_elec")
    texte = " ".join(_pages(run_audit(house, aujourd_hui=AUJOURD_HUI)))
    assert "Votre contrat" in texte and "Votre abonnement est de 9 kVA" in texte
    assert "rénovation d'ampleur (au moins deux classes" in texte
    assert "cela fait échouer le projet" in texte


@pytest.mark.parametrize("nom", ["audit_v21.json", "audit_v22.json", "audit_v23.json"])
def test_les_audits_stockes_se_lisent_encore(pdf_tmp, nom):
    import json
    audit = json.loads((Path(__file__).parent / "fixtures" / nom).read_text(encoding="utf-8"))
    texte = " ".join(_pages(audit))
    assert "Pourquoi :" not in texte and "kg/an" not in texte  # rien d'inventé pour un ancien audit
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 19), json_result=audit))
    assert ctx["climat"] is None and ctx["contrat"] is None


# --- Lot 5 (v2.5) : la vraie raison d'un « à l'occasion » ------------------------------------

from app.core.config import settings  # noqa: E402
from app.services import audit_engine as moteur  # noqa: E402


def maisons_lot5() -> dict:
    return {
        "reference": reference_complete(),
        "fioul": maison_type(),
        "fioul_F": maison_type(dpe_lettre="F", surface_habitable=150, isolation_murs="aucune", conso_elec_kwh_an=None),
        "convecteurs": maison_type(chauffage_principal="elec_direct", conso_elec_kwh_an=None),
    }


def _seule(house, cle: str) -> dict:
    """L'action chiffrée seule, sur la maison actuelle (premier passage de `planifier`)."""
    t = moteur._Trace()
    p = moteur._profil(house, t, AUJOURD_HUI)
    c = moteur.consommation(house, p, t)
    a = next(x for x in moteur._actions_candidates(house, p, moteur.deperditions(house), t) if x["action"] == cle)
    moteur._appliquer([a], c["conso_chauffage_retenue_kwh_an"], c["energie_chauffage"],
                      c["prix_energie_eur_kwh"], p["chauffage"], p["kva"])
    return a


def test_reference_occasion_par_chauffage_peu_cher(ref_audit):
    for cle in ("isolation_combles", "isolation_murs", "isolation_plancher"):
        assert _action(ref_audit, cle)["raison_occasion"] == "chauffage_peu_cher", cle


def test_fioul_murs_trop_chers():
    house = maison_type()
    murs = _action(run_audit(house, aujourd_hui=AUJOURD_HUI), "isolation_murs")
    assert murs["raison_occasion"] == "trop_cher"
    assert _seule(house, "isolation_murs")["temps_retour_ans"] > settings.audit_horizon_retour_max_ans


def test_fioul_fenetres_apres_les_autres():
    """Seules, les fenêtres se rembourseraient ; après la régulation, le toit et la PAC, non."""
    house = maison_type()
    fen = _action(run_audit(house, aujourd_hui=AUJOURD_HUI), "menuiseries")
    assert fen["horizon"] == "a_l_occasion" and fen["raison_occasion"] == "apres_autres"
    assert _seule(house, "menuiseries")["temps_retour_ans"] <= settings.audit_horizon_retour_max_ans


def test_seules_les_actions_a_l_occasion_ont_une_raison():
    for house in maisons_lot5().values():
        for a in run_audit(house, aujourd_hui=AUJOURD_HUI)["priorites"]:
            attendu = a["horizon"] == "a_l_occasion" and a["categorie"] == "chauffage"
            assert ("raison_occasion" in a) is attendu, a["action"]
            assert not any(k.startswith("_") for k in a), a["action"]


# --- Lot 5, étape 2 : le texte de la vraie raison -------------------------------------------

def test_les_nouvelles_cles_sont_couvertes_par_la_source_unique():
    cles = {c for t in ref.TEXTES_ACTIONS.values() for c in t}
    assert {"pourquoi_apres_autres", "pourquoi_trop_cher", "pourquoi_occasion", "pourquoi_rentable_inconnu",
            "pourquoi_rentable_convecteurs", "benefices_convecteurs", "devis_convecteurs",
            "vigilance_si_pac"} <= cles
    assert set(ref.LIBELLE_AVANT) == {k for k in ref.ACTIONS if k != "ballon_thermodynamique"}


def test_apres_autres_cite_les_actions_d_avant():
    fen = _action(run_audit(maison_type(), aujourd_hui=AUJOURD_HUI), "menuiseries")
    assert fen["raison_occasion"] == "apres_autres"
    assert fen["pourquoi"] is None or "Après" not in fen["pourquoi"]  # fenêtres : pas de texte « après »
    pac = _action(run_audit(maison_type(chauffage_principal="elec_direct", conso_elec_kwh_an=None),
                            aujourd_hui=AUJOURD_HUI), "pac_air_air")
    assert pac["raison_occasion"] == "apres_autres"
    assert pac["pourquoi"].startswith("Après la régulation et l'isolation du toit, votre maison")


def test_trop_cher_ne_dit_jamais_que_le_chauffage_coute_peu():
    murs = _action(run_audit(maison_type(), aujourd_hui=AUJOURD_HUI), "isolation_murs")
    assert murs["pourquoi"].startswith("Isoler les murs coûte cher au m² : même avec une chaudière fioul")


@pytest.mark.parametrize("nom", ["reference", "fioul", "fioul_F", "convecteurs"])
def test_garde_fou_aucun_chauffage_cher_ne_lit_vous_coute_peu(nom):
    r = run_audit(maisons_lot5()[nom], aujourd_hui=AUJOURD_HUI)
    textes = " ".join(a.get("pourquoi") or "" for a in r["priorites"])
    if r["consommation"]["cout_chauffage_actuel_eur"] > settings.audit_chauffage_peu_cher_eur:
        assert "vous coûte peu" not in textes and "chauffe peu" not in textes
    assert not re.search(r"\{[a-z_]+\}", repr(r))


def test_la_pac_des_convecteurs_parle_d_electricite():
    r = run_audit(maison_type(chauffage_principal="elec_direct"), aujourd_hui=AUJOURD_HUI)
    pac = _action(r, "pac_air_air")
    texte = " ".join([pac.get("pourquoi") or "", *pac["benefices"], *pac["vigilance"], *pac["devis"]])
    for interdit in ("chaudière", "CO₂", "désembouage", "loi d'eau"):
        assert interdit not in texte, interdit
    # Classée « maintenant » ou « prioritaire », elle dit son texte des convecteurs.
    vite = run_audit(maison_type(chauffage_principal="elec_direct", isolation_combles="bonne", regulation="connecte",
                                 menuiseries="double", conso_elec_kwh_an=None), aujourd_hui=AUJOURD_HUI)
    pac = _action(vite, "pac_air_air")
    if pac["horizon"] != "a_l_occasion":
        assert pac["pourquoi"] == ref.TEXTES_ACTIONS["pac_air_air"]["pourquoi_rentable_convecteurs"]


@pytest.mark.parametrize("chauffage, pac", [("fioul", False), ("gaz", False), ("elec_direct", False),
                                              ("PAC_air_air", True), ("PAC_air_eau", True)])
def test_la_regulation_ne_parle_de_pac_qu_aux_pac(chauffage, pac):
    reg = _action(run_audit(maison_type(chauffage_principal=chauffage), aujourd_hui=AUJOURD_HUI), "regulation")
    assert ("pompe à chaleur" in " ".join(reg["vigilance"])) is pac


def test_des_fenetres_inconnues_ne_sont_pas_du_simple_vitrage():
    r = run_audit(maison_type(menuiseries=None, regulation="connecte", isolation_combles="bonne"),
                  aujourd_hui=AUJOURD_HUI)
    fen = _action(r, "menuiseries")
    assert not (fen["pourquoi"] or "").startswith("Du simple vitrage")
    if fen["horizon"] != "a_l_occasion":
        assert fen["pourquoi"].startswith("Vos fenêtres ne sont pas renseignées")


def test_un_seul_arrondi_pour_le_cout_cite():
    """Le même coût partout : arrondi à la dizaine dans le message comme dans le pourquoi ; un coût
    de 426 € est cité 430 dans le message comme dans le pourquoi."""
    r = run_audit(reference_complete(conso_elec_kwh_an=9030), aujourd_hui=AUJOURD_HUI)  # 426 € → 430
    cout = moteur.cout_cite(r["consommation"]["cout_chauffage_actuel_eur"])
    message = r["synthese"]["message_sans_isolation"]
    assert f"environ {cout} €/an" in message
    combles = _action(r, "isolation_combles")
    assert f"environ {cout} €/an de chauffage" in combles["pourquoi"]
    montants = set(re.findall(r"(\d[\d ]*) €/an", message + " " + combles["pourquoi"]))
    assert montants == {cout}
