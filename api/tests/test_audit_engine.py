"""Le moteur de pré-audit v2, sur des maisons dont les chiffres clés sont refaits à la main.

Les valeurs attendues ne sont pas recopiées depuis une exécution du moteur : elles sont
calculées ci-dessous à partir des tables (`audit_reference.py`) et de `config.py`. Si une
table change, le test casse — c'est voulu : un chiffre de pré-audit qui bouge doit être
regardé, pas avalé.
"""

from datetime import datetime
from types import SimpleNamespace
from typing import get_args

import pytest

from app.core.config import settings
from app.models.house import House
from app.schemas import house as schema
from app.services import audit_reference as ref
from app.services import pdf_audit
from app.services.audit_engine import run_audit, zone_climatique
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
    assert settings.audit_version == "v2"


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
    Coût 100 m² × 25-70 € = 2 500-7 000, central 4 750 ; aides 15 %-45 % → 712-2 138 ;
    reste central 4 750 − 1 425 = 3 325 → retour 3 325 / 497,9 = 6,7 ans → prioritaire.
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
    assert combles["aide_estimee_eur"] == {"bas": 712, "haut": 2138}
    assert combles["reste_a_charge_eur"] == {"bas": 2612, "haut": 4038}
    assert combles["aides_statut"] == "a_verifier"
    assert combles["temps_retour_ans"] == 6.7


def test_combinaison_sequentielle():
    """Le total n'est pas la somme des gains isolés, et ne dépasse jamais le coût actuel."""
    r = run_audit(maison_type())
    c, s = r["consommation"], r["synthese"]
    total = s["economie_annuelle_totale_eur"]["central"]
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


def test_un_audit_v2_genere_son_pdf_et_un_contexte_resserre(pdf_dans_tmp):
    r = run_audit(cas_du_04_10_2026())
    assert pdf_audit.build_pdf(r, house_label="maison - 83000").exists()
    ctx = build_audit_context(SimpleNamespace(created_at=datetime(2026, 10, 19), json_result=r))
    assert ctx["version"] == "v2"
    assert ctx["consommation"]["message_ratio"]
    assert all("horizon" in a for a in ctx["priorites"])
    assert ctx["hypotheses"] and "a_l_occasion" in ctx["consigne"]


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
