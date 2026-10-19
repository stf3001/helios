"""Le moteur de pré-audit, sur une maison type dont chaque chiffre est refait à la main.

Les valeurs attendues ne sont pas recopiées depuis une exécution du moteur : elles sont
calculées ci-dessous à partir des tables (`audit_reference.py`) et de `config.py`. Si une
table change, le test casse — c'est voulu : un chiffre de pré-audit qui bouge doit être
regardé, pas avalé.

Hypothèses lues dans le code au 19/10/2026 : prix du kWh 0,20 € (`solar_prix_achat_eur_kwh`),
fourchettes à ±15 % (`audit_incertitude`).
"""

import pytest

from app.core.config import settings
from app.models.house import House
from app.services.audit_engine import run_audit
from app.services.completeness import niveau_for_score


def maison_type(**kw) -> House:
    """Maison de 100 m² construite entre 1975 et 1988, sans DPE, chauffée au fioul.

    Combles non isolés, murs partiellement isolés, plancher bien isolé, simple vitrage,
    VMC simple flux, aucune régulation, 8 000 kWh/an déclarés.
    """
    champs = dict(
        code_postal="13001", annee_construction="1975_1988", surface_habitable=100,
        isolation_combles="aucune", isolation_murs="partielle", isolation_plancher="bonne",
        menuiseries="simple", ventilation="VMC_simple", chauffage_principal="fioul",
        regulation="aucune", conso_elec_kwh_an=8000, objectifs=["améliorer le confort"],
    )
    champs.update(kw)
    return House(**champs)


@pytest.fixture
def audit():
    return run_audit(maison_type())


def test_les_hypotheses_du_calcul_a_la_main_tiennent():
    """Si l'une bouge, tous les chiffres ci-dessous sont à refaire — on le dit tout de suite."""
    assert settings.solar_prix_achat_eur_kwh == 0.20
    assert settings.audit_incertitude == 0.15


def test_deperditions(audit):
    """Part de base (ADEME) × coefficient de l'état réel, puis renormalisation.

        toiture          0,28 × 1,0 (aucune)      = 0,280
        murs             0,23 × 0,6 (partielle)   = 0,138
        air_ventilation  0,22 × 0,7 (VMC simple)  = 0,154
        menuiseries      0,13 × 1,0 (simple)      = 0,130
        plancher         0,09 × 0,3 (bonne)       = 0,027
        ponts_thermiques 0,05 × 0,7 (fixe)        = 0,035
                                          total   = 0,764

    0,280 / 0,764 = 36,6 %, 0,154 → 20,2 %, 0,138 → 18,1 %, 0,130 → 17,0 %,
    0,035 → 4,6 %, 0,027 → 3,5 %. Rangées de la plus forte à la plus faible.
    """
    assert audit["deperditions"] == [
        {"poste": "toiture", "part_pct": 36.6},
        {"poste": "air_ventilation", "part_pct": 20.2},
        {"poste": "murs", "part_pct": 18.1},
        {"poste": "menuiseries", "part_pct": 17.0},
        {"poste": "ponts_thermiques", "part_pct": 4.6},
        {"poste": "plancher", "part_pct": 3.5},
    ]
    assert sum(d["part_pct"] for d in audit["deperditions"]) == pytest.approx(100, abs=0.2)


def test_consommation_theorique(audit):
    """Pas de DPE : besoin pris sur l'année, 280 kWh/m²/an pour 1975-1988.

    280 × 100 m² = 28 000 kWh théoriques ; écart (8 000 − 28 000) / 28 000 = −71 %.
    """
    conso = audit["consommation"]
    assert conso["besoin_kwh_m2_an"] == 280
    assert conso["origine_besoin"] == "annee_construction"
    assert conso["conso_chauffage_theorique_kwh_an"] == 28000
    assert conso["ecart_pct"] == -71


def test_le_dpe_prime_sur_l_annee():
    audit = run_audit(maison_type(dpe_lettre="E"))
    assert audit["consommation"]["besoin_kwh_m2_an"] == 330
    assert audit["consommation"]["origine_besoin"] == "dpe"


def test_chiffrage_action_par_action(audit):
    """Économie = 8 000 kWh déclarés × gain du poste × 0,20 €. Aide sur le coût central.

    Le plancher (bien isolé) et la ventilation (VMC simple, pas « aucune/naturelle ») ne
    sont pas proposés. Restent cinq actions :

    régulation   forfait 150-500       central 325   aide 0 %  → 0      reste 325
                 8 000 × 8 %  = 640 kWh → 128 €/an   retour 325 / 128   = 2,5 ans
    combles      100 m² × 25-70        central 4 750 aide 45 % → 2 138  reste 2 612
                 (4 750 × 0,45 = 2 137,5, arrondi au pair)
                 8 000 × 20 % = 1 600 kWh → 320 €/an retour 2 612 / 320 = 8,2 ans
    murs         100 m² × 90-180       central 13 500 aide 40 % → 5 400 reste 8 100
                 8 000 × 18 % = 1 440 kWh → 288 €/an retour 8 100 / 288 = 28,1 ans
    menuiseries  100 / 15 = 6,7 → 7 fenêtres × 500-800  central 4 550  aide 25 % → 1 138
                 (1 137,5 arrondi au pair)  reste 3 412
                 8 000 × 10 % = 800 kWh → 160 €/an  retour 3 412 / 160 = 21,3 ans
    PAC air/eau  forfait 12 000-18 000 central 15 000 aide 40 % → 6 000 reste 9 000
                 8 000 × 25 % = 2 000 kWh → 400 €/an retour 9 000 / 400 = 22,5 ans
    """
    par_action = {a["action"]: a for a in audit["priorites"]}
    assert set(par_action) == {"regulation", "isolation_combles", "isolation_murs",
                               "menuiseries", "pac_air_eau"}

    attendu = {
        #                    coût bas, haut, aide, reste, €/an, retour
        "regulation":        (150, 500, 0, 325, 128, 2.5),
        "isolation_combles": (2500, 7000, 2138, 2612, 320, 8.2),
        "isolation_murs":    (9000, 18000, 5400, 8100, 288, 28.1),
        "menuiseries":       (3500, 5600, 1138, 3412, 160, 21.3),
        "pac_air_eau":       (12000, 18000, 6000, 9000, 400, 22.5),
    }
    for code, (bas, haut, aide, reste, eur, retour) in attendu.items():
        a = par_action[code]
        assert a["cout_eur"] == {"bas": bas, "haut": haut}, code
        assert a["aide_estimee_eur"] == aide, code
        assert a["reste_a_charge_eur"] == reste, code
        assert a["economie_annuelle_eur"]["central"] == eur, code
        assert a["temps_retour_ans"] == retour, code

    # Fourchette ±15 % : 320 → 272 / 368.
    assert par_action["isolation_combles"]["economie_annuelle_eur"] == {
        "bas": 272, "haut": 368, "central": 320}
    # La part de déperdition du poste est reprise telle quelle.
    assert par_action["isolation_combles"]["part_deperdition_pct"] == 36.6


def test_synthese(audit):
    """Investissement 150 + 2 500 + 9 000 + 3 500 + 12 000 = 27 150 € (bas)
    et 500 + 7 000 + 18 000 + 5 600 + 18 000 = 49 100 € (haut).
    Aides 0 + 2 138 + 5 400 + 1 138 + 6 000 = 14 676 €.
    Économies 128 + 320 + 288 + 160 + 400 = 1 296 €/an, soit 1 102 / 1 490 à ±15 %.
    """
    s = audit["synthese"]
    assert s["nb_actions"] == 5
    assert s["investissement_eur"] == {"bas": 27150, "haut": 49100}
    assert s["aides_estimees_eur"] == 14676
    assert s["economie_annuelle_totale_eur"] == {"bas": 1102, "haut": 1490, "central": 1296}
    assert s["premiere_action"] == "Thermostat programmable / régulation"


def test_priorisation_par_defaut_suit_la_hierarchie_puis_la_deperdition(audit):
    """Sobriété (1) → enveloppe (2) → systèmes (3). Dans l'enveloppe, la plus forte part
    de déperdition d'abord : combles 36,6 > murs 18,1 > menuiseries 17,0."""
    assert [a["action"] for a in audit["priorites"]] == [
        "regulation", "isolation_combles", "isolation_murs", "menuiseries", "pac_air_eau"]
    assert [a["rang"] for a in audit["priorites"]] == [1, 2, 3, 4, 5]


def test_l_objectif_facture_range_l_enveloppe_par_temps_de_retour():
    """Même maison, objectif « réduire ma facture » : dans l'enveloppe, le meilleur temps
    de retour d'abord — combles 8,2 < menuiseries 21,3 < murs 28,1. Les menuiseries passent
    devant les murs. La hiérarchie, elle, ne bouge pas : la sobriété reste première."""
    audit = run_audit(maison_type(objectifs=["Réduire ma facture"]))
    assert [a["action"] for a in audit["priorites"]] == [
        "regulation", "isolation_combles", "menuiseries", "isolation_murs", "pac_air_eau"]


def test_score_et_niveau_de_la_maison_type(audit):
    """Blocs remplis : identité 2/7 (année, surface) → 28,6 % × 20 = 5,72 ;
    enveloppe 5/6 (sans DPE) → 83,3 % × 25 = 20,83 ; systèmes 2/4 → 50 % × 25 = 12,5 ;
    énergie 1/3 → 33,3 % × 15 = 5,0 ; projet 1/3 → 5,0. Total 49,0 → qualitatif."""
    assert audit["completeness_score"] == 49.0
    assert audit["niveau"] == "prediagnostic_qualitatif"


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
