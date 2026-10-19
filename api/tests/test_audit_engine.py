"""Le moteur de pré-audit v2, sur des maisons dont les chiffres clés sont refaits à la main.

Les valeurs attendues ne sont pas recopiées depuis une exécution du moteur : elles sont
calculées ci-dessous à partir des tables (`audit_reference.py`) et de `config.py`. Si une
table change, le test casse — c'est voulu : un chiffre de pré-audit qui bouge doit être
regardé, pas avalé.
"""

import re
from datetime import date, datetime
from types import SimpleNamespace
from typing import get_args

import pytest

from app.core.config import settings
from app.models.house import House
from app.schemas import house as schema
from app.services import audit_reference as ref
from app.services import pdf_audit
from app.services.audit_engine import resume_etude_simulateur, run_audit, zone_climatique
from app.services.completeness import niveau_for_score
from app.services.rag import build_audit_context
from app.services.regions import TOUS_DEPARTEMENTS


def maison_type(**kw) -> House:
    """Maison de 100 m² à Marseille (H3), 1975-1988, sans DPE, chauffée au fioul.

    Combles non isolés, murs partiellement isolés, plancher bien isolé, simple vitrage,
    VMC simple flux, aucune régulation.
    """
    champs = dict(
        code_postal="13001", annee_construction="1975_1988", surface_habitable=100,
        isolation_combles="aucune", isolation_murs="partielle", isolation_plancher="bonne",
        menuiseries="simple", ventilation="VMC_simple", chauffage_principal="fioul",
        regulation="aucune", conso_elec_kwh_an=8000, objectifs=["confort_hiver"],
    )
    champs.update(kw)
    return House(**champs)


def cas_du_04_10_2026(**kw) -> House:
    """Le pré-audit réel qui annonçait 48 000 kWh, −81 % et des retours de 50 ans."""
    champs = dict(
        code_postal="83000", type_logement="maison", dpe_lettre="D", surface_habitable=200,
        nb_niveaux=2, chauffage_principal="PAC_air_eau", conso_elec_kwh_an=9000,
        isolation_combles="partielle", isolation_murs="partielle", menuiseries="double",
        ventilation="VMC_simple",
    )
    champs.update(kw)
    return House(**champs)


def test_les_hypotheses_du_calcul_a_la_main_tiennent():
    """Si l'une bouge, les chiffres ci-dessous sont à refaire — on le dit tout de suite."""
    assert dict(settings.audit_prix_energie_eur_kwh)["fioul"] == 0.19
    assert dict(settings.audit_prix_energie_eur_kwh)["gaz"] == 0.1456
    assert dict(settings.audit_rendement_chauffage)["fioul"] == 0.85
    assert dict(settings.audit_coef_zone)["H3"] == 0.55
    assert ref.ANNEE_BESOIN_UTILE_KWH_M2_AN["1975_1988"] == 180
    assert settings.audit_incertitude == 0.15
    assert settings.audit_version == "v2.1"


# --- Couverture du schéma : aucun repli silencieux -----------------------------------------

@pytest.mark.parametrize("literal, tables", [
    (schema.AnneeConstruction, [ref.ANNEE_BESOIN_UTILE_KWH_M2_AN]),
    (schema.NiveauIsolation, [ref.QUALITE_ISOLATION, ref.ISOLATION_A_TRAITER]),
    (schema.Menuiseries, [ref.QUALITE_MENUISERIES, ref.MENUISERIES_A_REMPLACER]),
    (schema.Ventilation, [ref.QUALITE_VENTILATION, ref.VENTILATION_A_REMPLACER]),
    (schema.Chauffage, [ref.ENERGIE_CHAUFFAGE, dict(settings.audit_part_chauffage_dpe),
                        dict(settings.audit_rendement_chauffage)]),
    (schema.Ecs, [dict(settings.simu_conso_ecs_kwh_occupant_an)]),
    (schema.Regulation, [ref.REGULATION_A_AMELIORER]),
    (schema.DpeLettre, [ref.DPE_KWH_EP_M2_AN]),
])
def test_chaque_valeur_du_schema_a_son_entree(literal, tables):
    for table in tables:
        manquantes = set(get_args(literal)) - set(table)
        assert not manquantes, manquantes


def test_chaque_energie_a_son_coefficient_et_son_prix():
    prix = dict(settings.audit_prix_energie_eur_kwh)
    for energie in set(ref.ENERGIE_CHAUFFAGE.values()):
        assert energie in dict(settings.audit_coef_ep_ef)
        assert energie == "electricite" or energie in prix


def test_les_defauts_sont_des_valeurs_du_schema():
    assert ref.ANNEE_DEFAUT in get_args(schema.AnneeConstruction)
    assert ref.CHAUFFAGE_DEFAUT in get_args(schema.Chauffage)
    assert settings.audit_ecs_defaut in get_args(schema.Ecs)
    assert ref.CHAUFFAGE_A_REMPLACER <= set(get_args(schema.Chauffage))


def test_chaque_departement_a_sa_zone_climatique():
    """Les 96 départements métropolitains, ni plus ni moins (arrêté du 26/10/2010)."""
    assert set(ref.ZONE_CLIMATIQUE) == set(TOUS_DEPARTEMENTS)
    assert zone_climatique("83000") == ("H3", False)
    assert zone_climatique("59000") == ("H1", False)
    assert zone_climatique("29200") == ("H2", False)
    assert zone_climatique("20000") == ("H3", False)  # Corse-du-Sud
    assert zone_climatique(None) == (settings.audit_zone_defaut, True)


# --- Le cas réel du 04/10/2026 -------------------------------------------------------------

def test_cas_de_reference_ne_produit_plus_48000_kwh():
    """DPE D = 215 kWh EP/m² (milieu de classe) × 200 m² / 1,9 × 0,50 (part PAC) = 11 316 kWh EF.

    Usages courants, 3 occupants supposés : 900 + 3 × 450 + 3 × 800 (ballon) = 4 650 kWh.
    Chauffage d'après la facture : 9 000 − 4 650 = 4 350 kWh. Rapport 4 350 / 11 316 = 0,38.
    """
    r = run_audit(cas_du_04_10_2026())
    c = r["consommation"]
    assert 3000 <= c["conso_chauffage_estimee_kwh_an"] <= 12000
    assert c["conso_chauffage_estimee_kwh_an"] == 11316
    assert c["origine"] == "dpe"
    assert c["zone_climatique"] == "H3"
    assert c["usages_specifiques_kwh_an"] == 4650
    assert c["conso_chauffage_declaree_kwh_an"] == 4350
    assert c["base_economies"] == "declaree"
    assert c["ratio_reel_theorique"] == 0.38
    assert c["message_ratio"] == settings.audit_ratio_messages[0][1]
    assert "ecart_pct" not in c

    for a in r["priorites"]:
        if a["horizon"] == "prioritaire":
            assert a["temps_retour_ans"] <= settings.audit_horizon_retour_max_ans
    assert all(a["horizon"] != "prioritaire" or a["temps_retour_ans"] <= 20 for a in r["priorites"])
    # Avec une PAC et 4 350 kWh de chauffage, l'isolation ne se rembourse pas seule.
    occasion = [a for a in r["priorites"] if a["horizon"] == "a_l_occasion"]
    assert occasion and all(a["libelle_occasion"] for a in occasion)
    assert r["synthese"]["premiere_action"] == "Thermostat programmable / régulation"


def test_combles_et_plancher_sur_l_emprise_murs_au_m2_de_mur():
    """200 m² sur 2 niveaux : 100 m² de combles, 200 × 0,85 = 170 m² de murs."""
    r = run_audit(cas_du_04_10_2026(isolation_plancher="aucune"))
    q = {a["action"]: a["quantite"] for a in r["priorites"]}
    assert q["isolation_combles"] == {"valeur": 100, "unite": "m²"}
    assert q["isolation_plancher"] == {"valeur": 100, "unite": "m²"}
    assert q["isolation_murs"] == {"valeur": 170, "unite": "m² de mur"}


# --- Maison au fioul : la séquence refaite à la main ---------------------------------------

def test_consommation_sans_dpe_corrigee_du_climat():
    """180 kWh/m² utiles × 100 m² × 0,55 (H3) / 0,85 (fioul) = 11 647 kWh de fioul.
    Pas de relevé de fioul exploitable : les économies portent sur l'estimation.
    11 647,06 × 0,19 € = 2 213 €/an."""
    c = run_audit(maison_type())["consommation"]
    assert c["conso_chauffage_estimee_kwh_an"] == 11647
    assert c["origine"] == "annee_construction"
    assert c["energie_chauffage"] == "fioul"
    assert c["base_economies"] == "estimee"
    assert c["ratio_reel_theorique"] is None  # la facture d'électricité ne dit rien du fioul
    assert c["cout_chauffage_actuel_eur"] == 2213


def test_les_deux_premieres_actions_a_la_main():
    """Régulation d'abord (sobriété) : 11 647,06 × 10 % × 0,19 = 221 €/an, retour 325 / 221,3 = 1,5 an.

    Puis les combles, sur ce qui reste : 10 482,35 × 25 % = 2 620,6 kWh × 0,19 = 498 €/an.
    Coût 100 m² × 25-70 € = 2 500-7 000, central 4 750 ; aides 0-25 €/m² → 0-2 500 ;
    reste bas max(0, 2 500 − 2 500) = 0, haut 7 000 − 0 = 7 000 ;
    reste central 4 750 − 1 250 = 3 500 → retour 3 500 / 497,9 = 7,0 ans → prioritaire.
    """
    p = run_audit(maison_type())["priorites"]
    assert [a["action"] for a in p[:2]] == ["regulation", "isolation_combles"]
    reg, combles = p[0], p[1]
    assert reg["horizon"] == "maintenant"
    assert reg["economie_annuelle_eur"]["central"] == 221
    assert reg["temps_retour_ans"] == 1.5
    assert combles["horizon"] == "prioritaire"
    assert combles["economie_annuelle_kwh"] == 2621
    assert combles["economie_annuelle_eur"]["central"] == 498
    assert combles["aide_estimee_eur"] == {"bas": 0, "haut": 2500}
    assert combles["reste_a_charge_eur"] == {"bas": 0, "haut": 7000}
    assert combles["aides_statut"] == "base_connaissances"
    assert "CEE" in combles["aide_note"]
    assert combles["temps_retour_ans"] == 7.0


def test_combinaison_sequentielle():
    """Le total n'est pas la somme des gains isolés, et ne dépasse jamais le coût actuel."""
    r = run_audit(maison_type())
    c, s = r["consommation"], r["synthese"]
    total = s["economie_chauffage_eur"]["central"]
    marginales = sum(a["economie_annuelle_eur"]["central"] for a in r["priorites"])
    assert total == pytest.approx(marginales, abs=len(r["priorites"]))  # arrondis

    # Chaque action prise seule, sur la maison d'origine (sans PAC : énergie inchangée).
    isoles = sum(c["conso_chauffage_retenue_kwh_an"] * a["gain_pct_chauffage"] * c["prix_energie_eur_kwh"]
                 for a in r["priorites"] if a["gain_pct_chauffage"] is not None)
    enveloppe = sum(a["economie_annuelle_eur"]["central"] for a in r["priorites"]
                    if a["gain_pct_chauffage"] is not None)
    assert enveloppe < isoles
    assert total <= c["cout_chauffage_actuel_eur"]


def test_aucune_action_a_l_occasion_n_est_une_priorite():
    for house in (maison_type(), cas_du_04_10_2026(), maison_type(objectifs=["reduire_facture"])):
        r = run_audit(house)
        horizons = [ref.HORIZONS.index(a["horizon"]) for a in r["priorites"]]
        assert horizons == sorted(horizons)
        for a in r["priorites"]:
            if a["horizon"] == "prioritaire":
                assert a["temps_retour_ans"] <= settings.audit_horizon_retour_max_ans
                assert a["temps_retour_ans"] <= a["duree_vie_ans"]
            if a["horizon"] != "a_l_occasion":
                assert a["libelle_occasion"] is None
        premiere = r["synthese"]["premiere_action"]
        if premiere:
            assert next(a for a in r["priorites"] if a["label"] == premiere)["horizon"] != "a_l_occasion"


# --- Gaz, convecteurs, maisons récentes, climat --------------------------------------------

def test_maison_au_gaz_economise_du_gaz_au_prix_du_gaz():
    """180 × 100 × 0,55 / 0,9 = 11 000 kWh de gaz. Régulation : 1 100 kWh × 0,1456 = 160 €."""
    r = run_audit(maison_type(chauffage_principal="gaz"))
    c = r["consommation"]
    assert c["energie_chauffage"] == "gaz"
    assert c["prix_energie_eur_kwh"] == 0.1456
    assert c["conso_chauffage_estimee_kwh_an"] == 11000
    reg = r["priorites"][0]
    assert reg["action"] == "regulation"
    assert reg["energie_economisee"] == "gaz"
    assert reg["economie_annuelle_kwh"] == 1100
    assert reg["economie_annuelle_eur"]["central"] == 160
    assert "pac_air_eau" in {a["action"] for a in r["priorites"]}


def test_convecteurs_recoivent_la_pac():
    r = run_audit(maison_type(chauffage_principal="elec_direct"))
    pac = next(a for a in r["priorites"] if a["action"] == "pac_air_eau")
    assert pac["label"] == "Pompe à chaleur air/eau (remplacement du chauffage actuel)"
    assert pac["economie_annuelle_eur"]["central"] > 0


def test_une_pac_ne_recoit_pas_de_pac():
    assert "pac_air_eau" not in {a["action"] for a in run_audit(cas_du_04_10_2026())["priorites"]}


def test_maison_recente_n_est_pas_traitee_comme_une_maison_ancienne():
    """apres_2012 : 50 kWh/m² utiles (pas l'ancien repli de 280)."""
    c = run_audit(maison_type(annee_construction="apres_2012"))["consommation"]
    assert c["origine"] == "annee_construction"
    assert c["detail_estimation"]["besoin_utile_kwh_m2_an"] == 50
    assert c["conso_chauffage_estimee_kwh_an"] == round(50 * 100 * 0.55 / 0.85)


def test_meme_maison_en_h3_consomme_moins_qu_en_h1():
    h1 = run_audit(maison_type(code_postal="59000"))["consommation"]
    h3 = run_audit(maison_type(code_postal="13001"))["consommation"]
    assert h1["zone_climatique"] == "H1" and h3["zone_climatique"] == "H3"
    assert h3["conso_chauffage_estimee_kwh_an"] < h1["conso_chauffage_estimee_kwh_an"]


def test_facture_qui_ne_laisse_rien_au_chauffage_declenche_une_alerte():
    r = run_audit(cas_du_04_10_2026(conso_elec_kwh_an=4000))
    assert r["consommation"]["conso_chauffage_declaree_kwh_an"] == 0
    assert r["consommation"]["base_economies"] == "estimee"
    assert r["alertes"]


# --- Traçabilité ----------------------------------------------------------------------------

def test_entrees_hypotheses_et_statuts():
    r = run_audit(cas_du_04_10_2026())
    entrees = {e["champ"]: e for e in r["entrees"]}
    assert entrees["dpe_lettre"] == {"champ": "dpe_lettre", "valeur": "D", "statut": "declare"}
    assert entrees["nb_occupants"]["statut"] == "suppose"
    assert "3 occupants" in entrees["nb_occupants"]["hypothese"]
    assert entrees["isolation_plancher"]["statut"] == "suppose"

    cles = {h["cle"] for h in r["hypotheses"]}
    assert {"dpe_kwh_ep_m2_an[D]", "coef_ep_ef[electricite]", "part_chauffage_dpe[PAC_air_eau]",
            "prix_electricite_eur_kwh", "zone_climatique"} <= cles
    assert all({"cle", "valeur", "source", "date"} <= set(h) for h in r["hypotheses"])

    # Plancher inconnu : sa part de déperdition est supposée, et donc la répartition.
    dep = {d["poste"]: d for d in r["deperditions"]}
    assert dep["plancher"]["statut"] == "suppose"
    assert dep["toiture"]["statut"] == "calcule"
    assert r["deperditions_statut"] == "suppose"
    assert sum(d["part_pct"] for d in r["deperditions"]) == pytest.approx(100, abs=0.2)


def test_relevé_d_autre_energie_sans_unite_n_est_pas_utilise():
    r = run_audit(maison_type(conso_autre_energie_type="fioul", conso_autre_energie_qte=2000))
    assert r["consommation"]["base_economies"] == "estimee"
    assert "conso_autre_energie" in {h["cle"] for h in r["hypotheses"]}


# --- Compatibilité : un audit v1 stocké s'affiche toujours ---------------------------------

AUDIT_V1 = {
    "version_helios": "v1", "completeness_score": 72.0, "niveau": "preaudit_chiffre",
    "deperditions": [{"poste": "toiture", "part_pct": 36.6}, {"poste": "murs", "part_pct": 63.4}],
    "consommation": {"besoin_kwh_m2_an": 240, "origine_besoin": "dpe", "surface_m2": 200,
                     "conso_chauffage_theorique_kwh_an": 48000, "conso_elec_declaree_kwh_an": 9000,
                     "ecart_pct": -81},
    "priorites": [{"action": "regulation", "label": "Thermostat programmable / régulation",
                   "poste": "pilotage", "part_deperdition_pct": None, "cout_eur": {"bas": 150, "haut": 500},
                   "aide_estimee_eur": 0, "reste_a_charge_eur": 325,
                   "economie_annuelle_eur": {"bas": 122, "haut": 166, "central": 144},
                   "temps_retour_ans": 2.3, "priorite_hierarchie": 1, "rang": 1}],
    "synthese": {"nb_actions": 1, "investissement_eur": {"bas": 150, "haut": 500}, "aides_estimees_eur": 0,
                 "economie_annuelle_totale_eur": {"bas": 122, "haut": 166, "central": 144},
                 "premiere_action": "Thermostat programmable / régulation"},
    "avertissement": "…",
}


@pytest.fixture
def pdf_dans_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_audit, "PDF_DIR", tmp_path)
    return tmp_path


def test_un_audit_v1_genere_toujours_son_pdf_et_son_contexte(pdf_dans_tmp):
    out = pdf_audit.build_pdf(AUDIT_V1, house_label="maison - 83000")
    assert out.exists() and out.stat().st_size > 1000
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 4), json_result=AUDIT_V1))
    assert ctx["resultat"] == AUDIT_V1


# Un audit v2 tel qu'il a été stocké (moteur du lot 1, sans gestes ni solaire).
AUDIT_V2 = {
    "version_helios": "v2", "completeness_score": 40.6, "niveau": "prediagnostic_qualitatif",
    "entrees": [], "deperditions": [{"poste": "toiture", "part_pct": 100.0, "statut": "calcule"}],
    "consommation": {"conso_chauffage_estimee_kwh_an": 11316, "energie_chauffage": "electricite", "origine": "dpe",
                     "zone_climatique": "H3", "surface_m2": 200, "conso_elec_declaree_kwh_an": 9000,
                     "usages_specifiques_kwh_an": 4650, "conso_chauffage_declaree_kwh_an": 4350,
                     "ratio_reel_theorique": 0.38, "message_ratio": "Votre consommation réelle est plus basse.",
                     "conso_chauffage_retenue_kwh_an": 4350, "base_economies": "declaree",
                     "prix_energie_eur_kwh": 0.2001, "cout_chauffage_actuel_eur": 870, "statuts": {}},
    "priorites": [{"action": "regulation", "label": "Thermostat programmable / régulation", "rang": 1,
                   "cout_eur": {"bas": 150, "haut": 500}, "aide_estimee_eur": {"bas": 0, "haut": 0},
                   "reste_a_charge_eur": {"bas": 325, "haut": 325}, "aides_statut": "a_verifier",
                   "economie_annuelle_eur": {"bas": 74, "haut": 100, "central": 87}, "temps_retour_ans": 3.7,
                   "horizon": "maintenant", "libelle_occasion": None, "priorite_hierarchie": 1}],
    "synthese": {"nb_actions": 1, "investissement_eur": {"bas": 150, "haut": 500},
                 "aides_estimees_eur": {"bas": 0, "haut": 0}, "reste_a_charge_eur": {"bas": 325, "haut": 325},
                 "economie_annuelle_totale_eur": {"bas": 74, "haut": 100, "central": 87},
                 "premiere_action": "Thermostat programmable / régulation"},
    "alertes": [], "hypotheses": [{"cle": "zone_climatique", "valeur": "H3", "source": "x", "date": None}],
    "avertissement": "…",
}


def test_un_audit_v2_genere_son_pdf_et_un_contexte_resserre(pdf_dans_tmp):
    assert pdf_audit.build_pdf(AUDIT_V2, house_label="maison - 83000").exists()
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 19), json_result=AUDIT_V2))
    assert ctx["version"] == "v2"
    assert ctx["consommation"]["message_ratio"]
    assert all("horizon" in a for a in ctx["priorites"])
    assert ctx["hypotheses"] and "a_l_occasion" in ctx["consigne"]
    assert ctx["gestes_gratuits"] is None  # un v2 n'en a pas : rien d'inventé


# --- Score et niveaux (inchangés) -----------------------------------------------------------

@pytest.mark.parametrize("score, niveau", [
    (0, "conseils_generaux"),
    (39.9, "conseils_generaux"),
    (40, "prediagnostic_qualitatif"),
    (69.9, "prediagnostic_qualitatif"),
    (70, "preaudit_chiffre"),
    (100, "preaudit_chiffre"),
])
def test_bornes_des_niveaux(score, niveau):
    """40 % ouvre le pré-diagnostic (et la route API du chat), 70 % le pré-audit chiffré."""
    assert niveau_for_score(score) == niveau


# --- Lot 2 (v2.1) : un audit qui conseille --------------------------------------------------

AUJOURD_HUI = date(2026, 10, 19)


def reference_complete(**kw) -> House:
    """La maison de référence avec tout ce que la fiche sait dire."""
    champs = dict(
        code_postal="83000", type_logement="maison", dpe_lettre="D", surface_habitable=200, nb_niveaux=2,
        nb_occupants=4, chauffage_principal="PAC_air_air", chauffage_principal_annee=2010,
        chauffage_appoint="autre", ecs="ballon_elec", ecs_annee=2010, clim=True, clim_nb_pieces=4,
        regulation="thermostat", conso_elec_kwh_an=9000, isolation_combles="partielle",
        isolation_murs="partielle", menuiseries="double", ventilation="VMC_simple",
    )
    champs.update(kw)
    return House(**champs)


def etude(jour: str = "2026-09-01") -> dict:
    """Résumé tel que `resume_etude_simulateur` le produit, avec des chiffres d'étude ronds."""
    return {"date": jour, "version_moteur": "simu-2", "option": "6 kWc + pilotage", "puissance_kwc": 6.0,
            "investissement_eur": 10500, "economie_1re_annee_eur": 812, "temps_retour_ans": 12.9,
            "gain_net_25_ans_eur": 14230, "autonomie_pct": 41.5}


@pytest.fixture
def ref_sans_etude():
    return run_audit(reference_complete(), aujourd_hui=AUJOURD_HUI)


def test_reference_hypotheses_clim_et_appoint(ref_sans_etude):
    """Usages : 900 + 4 × 450 + 4 × 800 (ballon) + 4 pièces × 250 = 6 900 kWh, la clim
    comptée une seule fois. Chauffage d'après la facture : 9 000 − 6 900 = 2 100 kWh."""
    hyp = {h["cle"]: h["valeur"] for h in ref_sans_etude["hypotheses"]}
    assert "PAC air/air réversible" in hyp["clim_pac_reversible"]
    assert "appoint" in hyp["appoint_hors_facture"]
    assert ref_sans_etude["consommation"]["usages_specifiques_kwh_an"] == 6900
    assert ref_sans_etude["consommation"]["conso_chauffage_declaree_kwh_an"] == 2100
    assert "appoint d'une autre" in ref_sans_etude["consommation"]["message_ratio"]


def test_pac_air_air_sans_clim_declaree():
    r = run_audit(reference_complete(clim=False), aujourd_hui=AUJOURD_HUI)
    assert "pac_air_air_ete" in {h["cle"] for h in r["hypotheses"]}


def test_valeurs_par_defaut_dans_les_hypotheses():
    r = run_audit(reference_complete(nb_occupants=None, nb_niveaux=None, clim_nb_pieces=None),
                  aujourd_hui=AUJOURD_HUI)
    cles = {h["cle"] for h in r["hypotheses"] if h["source"] == "Fiche Maison"}
    assert {"nb_occupants", "nb_niveaux", "clim_nb_pieces"} <= cles


def test_reference_conseils_d_age(ref_sans_etude):
    """PAC air/air et ballon de 2010 : 16 ans pour 15 de durée de vie (seuil 80 % = 12)."""
    conseils = {c["equipement"]: c for c in ref_sans_etude["conseils_equipements"]}
    assert set(conseils) == {"PAC_air_air", "ballon_elec"}
    assert conseils["PAC_air_air"]["age_ans"] == 16
    assert "faites-la entretenir" in conseils["PAC_air_air"]["texte"]
    assert "une PAC récente consomme généralement moins" in conseils["PAC_air_air"]["texte"]
    assert "faites-le entretenir" in conseils["ballon_elec"]["texte"]


def test_reference_ballon_thermodynamique(ref_sans_etude):
    """(800 − 280) × 4 = 2 080 kWh × 0,2001 = 416 €/an. Ballon en fin de vie : surcoût
    1 500-2 500, central 2 000 ; aide 0-30 % (à vérifier) → 0-600 ; reste central 1 700 ;
    retour 1 700 / 416,2 = 4,1 ans → prioritaire."""
    b = next(a for a in ref_sans_etude["priorites"] if a["action"] == "ballon_thermodynamique")
    assert b["horizon"] == "prioritaire"
    assert b["base_cout"] == "surcout"
    assert b["cout_eur"] == {"bas": 1500, "haut": 2500}
    assert b["economie_annuelle_kwh"] == 2080
    assert b["economie_annuelle_eur"]["central"] == 416
    assert b["temps_retour_ans"] == 4.1
    assert b["contexte"] == "au remplacement de votre ballon, qui approche de sa fin de vie"
    assert b["aides_statut"] == "a_verifier"
    assert b["categorie"] == "eau_chaude"


def test_ballon_recent_chiffre_sur_le_cout_complet():
    r = run_audit(reference_complete(ecs_annee=2022), aujourd_hui=AUJOURD_HUI)
    b = next(a for a in r["priorites"] if a["action"] == "ballon_thermodynamique")
    assert b["base_cout"] == "cout_complet"
    assert b["cout_eur"] == {"bas": 2500, "haut": 4000}


def test_reference_piste_solaire_sans_chiffre(ref_sans_etude):
    sol = ref_sans_etude["solaire"]
    assert sol["type"] == "piste"
    assert sol["lien"] == "/simulateur-solaire"
    assert "9 000 kWh" in sol["texte"]
    assert re.findall(r"\d+", sol["texte"].replace("9 000", "")) == []  # aucun autre chiffre
    assert "production_solaire" not in {a["action"] for a in ref_sans_etude["priorites"]}


def test_reference_confort_d_ete_et_combles(ref_sans_etude):
    ete = ref_sans_etude["confort_ete"]
    assert len(ete["conseils"]) == 4
    assert ete["note_combles"] == ref.CONFORT_ETE_COMBLES


def test_reference_premiere_etape_et_decompte(ref_sans_etude):
    s = ref_sans_etude["synthese"]
    assert s["premiere_action"] == "Ballon d'eau chaude thermodynamique"
    assert s["premiere_action_type"] == "action"
    assert s["decompte"] == "1 action prioritaire, 3 à prévoir à l'occasion"
    assert s["message_sans_isolation"].startswith("Aucuns travaux d'isolation")


def test_reference_murs_sans_aide(ref_sans_etude):
    murs = next(a for a in ref_sans_etude["priorites"] if a["action"] == "isolation_murs")
    assert murs["aide_estimee_eur"] == {"bas": 0, "haut": 0}
    assert "rénovation d'ampleur" in murs["aide_note"]


def test_aide_pac_en_euros_selon_la_base():
    pac = next(a for a in run_audit(maison_type(), aujourd_hui=AUJOURD_HUI)["priorites"]
               if a["action"] == "pac_air_eau")
    assert pac["aide_estimee_eur"] == {"bas": 0, "haut": 5000}


def test_gestes_gratuits_presents_et_sans_chiffre(ref_sans_etude):
    gestes = ref_sans_etude["gestes"]
    assert gestes and "filtres_pac" in {g["cle"] for g in gestes}
    assert all(set(g) == {"cle", "texte"} for g in gestes)


def test_premiere_etape_jamais_vide():
    """Maison déjà bien traitée, sans piste solaire : la première étape est un geste."""
    r = run_audit(maison_type(isolation_combles="bonne", isolation_murs="bonne", menuiseries="triple",
                              regulation="connecte", chauffage_principal="PAC_air_eau"), aujourd_hui=AUJOURD_HUI)
    assert r["synthese"]["premiere_action"]
    assert r["synthese"]["premiere_action_type"] == "geste"


def test_eau_chaude_non_combinee_au_chauffage(ref_sans_etude):
    s = ref_sans_etude["synthese"]
    chauffage = sum(a["economie_annuelle_eur"]["central"] for a in ref_sans_etude["priorites"]
                    if a["categorie"] == "chauffage")
    assert s["economie_eau_chaude_eur"]["central"] == 416
    assert s["economie_chauffage_eur"]["central"] == pytest.approx(chauffage, abs=3)
    assert s["economie_annuelle_totale_eur"]["central"] == pytest.approx(
        s["economie_chauffage_eur"]["central"] + 416, abs=1)


@pytest.mark.parametrize("house", [maison_type(), cas_du_04_10_2026(), reference_complete(),
                                   maison_type(chauffage_principal="gaz", ecs="ballon_elec")])
def test_reste_a_charge_coherent(house):
    for a in run_audit(house, aujourd_hui=AUJOURD_HUI)["priorites"]:
        r = a["reste_a_charge_eur"]
        assert 0 <= r["bas"] <= r["haut"], a["action"]
        assert r["bas"] == max(0, a["cout_eur"]["bas"] - a["aide_estimee_eur"]["haut"])
        assert r["haut"] == a["cout_eur"]["haut"] - a["aide_estimee_eur"]["bas"]


def test_pas_de_confort_d_ete_en_h1():
    assert run_audit(reference_complete(code_postal="59000"), aujourd_hui=AUJOURD_HUI)["confort_ete"] is None


@pytest.mark.parametrize("kw", [{"type_logement": "appartement"}, {"conso_elec_kwh_an": 3500},
                                {"statut": "locataire"}])
def test_pas_de_piste_solaire_hors_cible(kw):
    assert run_audit(reference_complete(**kw), aujourd_hui=AUJOURD_HUI)["solaire"] is None


def test_etude_simulateur_citee_a_l_identique():
    r = run_audit(reference_complete(), etude_simulateur=etude(), aujourd_hui=AUJOURD_HUI)
    sol = next(a for a in r["priorites"] if a["action"] == "production_solaire")
    assert sol["priorite_hierarchie"] == 4
    assert sol["cout_eur"] == {"bas": 10500, "haut": 10500}
    assert sol["economie_annuelle_eur"] == {"bas": 812, "haut": 812, "central": 812}
    assert sol["temps_retour_ans"] == 12.9
    assert sol["statuts"]["economie_annuelle_eur"] == "calcule"
    assert sol["source"] == "simulateur, étude du 01/09/2026, moteur simu-2"
    assert sol["mention"] is None
    assert r["solaire"]["type"] == "etude" and r["solaire"]["etude"] == etude()
    # Jamais devant une action de sobriété, d'enveloppe ou de système du même horizon.
    meme = [a for a in r["priorites"] if a["horizon"] == sol["horizon"]]
    assert meme[-1]["action"] == "production_solaire"
    # Ses chiffres restent à part des travaux.
    sans = run_audit(reference_complete(), aujourd_hui=AUJOURD_HUI)["synthese"]
    assert r["synthese"]["investissement_eur"] == sans["investissement_eur"]
    assert r["synthese"]["economie_annuelle_totale_eur"] == sans["economie_annuelle_totale_eur"]


def test_etude_de_plus_de_six_mois_a_mettre_a_jour():
    r = run_audit(reference_complete(), etude_simulateur=etude("2026-03-01"), aujourd_hui=AUJOURD_HUI)
    assert r["solaire"]["a_mettre_a_jour"] is True
    sol = next(a for a in r["priorites"] if a["action"] == "production_solaire")
    assert sol["mention"] == "étude à mettre à jour"


def test_resume_etude_simulateur_recopie_le_resultat():
    stockee = SimpleNamespace(
        created_at=datetime(2026, 9, 1, 10, 30), version_moteur="simu-2", nom="6 kWc + pilotage",
        resultat={"indicateurs": {"puissance_kwc": 6.0, "economie_1re_annee_eur": 812, "temps_retour_ans": 12.9,
                                  "gain_net_25_ans_eur": 14230, "autonomie_pct": 41.5},
                  "investissement": {"total_eur": 10500}},
    )
    assert resume_etude_simulateur(stockee) == etude()


def test_un_audit_v21_genere_son_pdf_et_son_contexte(pdf_dans_tmp):
    r = run_audit(reference_complete(), etude_simulateur=etude(), aujourd_hui=AUJOURD_HUI)
    assert pdf_audit.build_pdf(r, house_label="maison - 83000").exists()
    r2 = run_audit(reference_complete(nb_occupants=None), aujourd_hui=AUJOURD_HUI)
    assert pdf_audit.build_pdf(r2, house_label="maison - 83000").exists()
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 19), json_result=r))
    assert ctx["premiere_etape"] == "Ballon d'eau chaude thermodynamique"
    assert ctx["gestes_gratuits"] and ctx["conseils_equipements"] and ctx["confort_ete"]
    assert ctx["solaire"]["type"] == "etude"
