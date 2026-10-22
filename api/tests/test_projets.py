"""Carnet, lot 9 : modèles de projet et recopie d'une étude — fonctions pures, sans base."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import projets as pj
from app.services.agents_engine import SOURCES
from app.services.parcours import parcours

MODELES = pj.charger_modeles()
SOURCES_KB = {s.name for s in SOURCES}
LE_12_10 = datetime(2026, 10, 12, 9, 30, tzinfo=timezone.utc)


def maison(**kw):
    champs = dict(statut="proprietaire", type_logement="maison", chauffage_principal=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def visibles(m=None, sources=SOURCES_KB):
    m = m or maison()
    return [x["id"] for x in pj.modeles_visibles(MODELES, m, parcours(m), sources)]


# — Les modèles —

ENVELOPPE = ["isolation-combles", "isolation-murs", "isolation-plancher", "fenetres", "ventilation", "regulation-chauffage"]


def test_les_seize_modeles_se_chargent():
    assert [m["id"] for m in MODELES] == [
        "panneaux-solaires", "batterie", "sortie-fioul-pac-air-eau", "sortie-gaz-pac-air-eau",
        "pac-air-air-convecteurs", "ballon-thermodynamique", "carport-solaire", "machine-eau-air",
        "eolienne-verticale", "jardin-hiver", *ENVELOPPE]


def test_un_modele_dont_une_fiche_manque_n_est_pas_servi():
    # Toutes les fiches existent depuis le point 51 (jardin d'hiver).
    assert all(not pj.fiches_manquantes(m, SOURCES_KB) for m in MODELES)
    assert "jardin-hiver" in visibles()
    assert "jardin-hiver" not in visibles(sources=SOURCES_KB - {"jardin_hiver"})
    # Une fiche retirée de la base fait disparaître ses modèles.
    assert "batterie" not in visibles(sources=SOURCES_KB - {"stockage_contrats"})


def test_le_locataire_ne_voit_pas_les_projets_lourds():
    # La régulation (souvent un thermostat) n'est pas un projet lourd.
    assert visibles(maison(statut="locataire")) == ["machine-eau-air", "regulation-chauffage"]


def test_appartement_et_chauffage_actuel():
    assert visibles(maison(type_logement="appartement")) == [
        "pac-air-air-convecteurs", "ballon-thermodynamique", "machine-eau-air",  # ni jardin d'hiver
        "fenetres", "ventilation", "regulation-chauffage"]  # ni combles, ni murs, ni plancher
    fioul = visibles(maison(chauffage_principal="fioul"))
    assert "sortie-fioul-pac-air-eau" in fioul and "sortie-gaz-pac-air-eau" not in fioul
    assert "pac-air-air-convecteurs" not in fioul
    # Chauffage non renseigné : rien n'est caché.
    assert {"sortie-fioul-pac-air-eau", "sortie-gaz-pac-air-eau", "pac-air-air-convecteurs"} <= set(visibles())


RETIRER = object()


@pytest.mark.parametrize("modif, motif", [
    ({"famille": "isolation"}, "famille"),
    ({"outil": "calculette"}, "outil"),
    ({"outil": "simulateur-solaire", "poste": RETIRER}, "poste"),
    ({"fiches_kb": []}, "fiches_kb"),
    ({"equipements_crees": [{"categorie": "ecs", "type": "PAC_air_eau"}]}, "équipement inconnu"),
    ({"masque_si": {"surface": [1]}}, "masque_si"),
    ({"lourd": RETIRER}, "lourd"),
    ({"prix": 1000}, "inconnu"),
])
def test_un_modele_mal_ecrit_est_refuse(tmp_path, modif, motif):
    m = {k: v for k, v in {**MODELES[0], **modif}.items() if v is not RETIRER}
    f = tmp_path / "m.json"
    f.write_text(json.dumps({"modeles": [m]}), encoding="utf-8")
    with pytest.raises(pj.ModeleInvalide, match=motif):
        pj.charger_modeles(f)


# — Recopie d'une étude : tel quel, aucun recalcul —

RESULTAT_SIMU = {
    "investissement": {"panneaux_eur": 10_521, "carport_eur": 0, "batterie_eur": 6_480, "inertie_eur": 0,
                       "eolien_eur": 0, "total_eur": 17_001},
    "indicateurs": {"economie_1re_annee_eur": 812},
}


def test_depuis_simulateur_recopie_le_poste_et_dit_le_perimetre():
    r = pj.depuis_simulateur(RESULTAT_SIMU, "panneaux_eur", LE_12_10, "e1")
    assert (r["budget_bas_eur"], r["budget_haut_eur"], r["economie_annuelle_eur"]) == (10_521, 10_521, 812)
    assert r["budget_date"] == r["economie_date"] == "2026-10-12"
    assert (r["budget_source"], r["budget_statut"], r["economie_statut"]) == ("etude", "suppose", "calcule")
    # L'économie porte aussi sur la batterie : le projet « panneaux » ne se l'attribue pas en silence.
    assert r["etude_ref"] == {"type": "simulateur", "id": "e1", "date": "2026-10-12",
                              "perimetre_economie": "ensemble", "autres_postes": ["batterie_eur"]}
    seul = {**RESULTAT_SIMU, "investissement": {**RESULTAT_SIMU["investissement"], "batterie_eur": 0}}
    assert pj.depuis_simulateur(seul, "panneaux_eur", LE_12_10, "e1")["etude_ref"]["perimetre_economie"] == "projet"


def test_une_etude_sans_ce_poste_ne_se_lie_pas():
    assert pj.depuis_simulateur(RESULTAT_SIMU, "eolien_eur", LE_12_10, "e1") is None


AUDIT = {"priorites": [
    {"action": "isolation_combles", "cout_eur": {"bas": 2500, "haut": 7000}},
    {"action": "ballon_thermodynamique", "cout_eur": {"bas": 1800, "haut": 2800},
     "economie_annuelle_eur": {"bas": 351, "haut": 475, "central": 413},
     "statuts": {"cout_eur": "suppose", "economie_annuelle_eur": "calcule"}},
]}


def test_depuis_audit_recopie_l_action():
    r = pj.depuis_audit(AUDIT, "ballon_thermodynamique", LE_12_10, "a1")
    assert (r["budget_bas_eur"], r["budget_haut_eur"], r["economie_annuelle_eur"]) == (1800, 2800, 413)
    assert (r["budget_source"], r["budget_statut"], r["economie_statut"]) == ("audit", "suppose", "calcule")
    assert r["etude_ref"]["action"] == "ballon_thermodynamique" and r["etude_ref"]["date"] == "2026-10-12"
    assert pj.depuis_audit(AUDIT, "pac_air_eau", LE_12_10, "a1") is None
    assert pj.depuis_audit({"actions": []}, "ballon_thermodynamique", LE_12_10, "a1") is None  # format v1


def test_sans_calculateur():
    sans = {m["id"] for m in MODELES if m["outil"] == "aucun"}
    assert sans == {"jardin-hiver", "machine-eau-air"}


def test_seuls_les_equipements_coches_sont_crees():
    pv = MODELES[0]
    assert pj.equipements_a_creer(pv, [1]) == [pv["equipements_crees"][1]]
    assert pj.equipements_a_creer(pv, []) == []
    with pytest.raises(ValueError):
        pj.equipements_a_creer(pv, [5])


# — Phase 2 : « Isolation et confort » —

def test_les_six_modeles_enveloppe_et_leurs_fiches():
    env = {m["id"]: m for m in MODELES if m["famille"] == "enveloppe"}
    assert list(env) == ENVELOPPE
    assert {i: m["outil"] for i, m in env.items()} == {
        "isolation-combles": "pre-audit:isolation_combles", "isolation-murs": "pre-audit:isolation_murs",
        "isolation-plancher": "pre-audit:isolation_plancher", "fenetres": "pre-audit:menuiseries",
        "ventilation": "pre-audit:ventilation_double_flux", "regulation-chauffage": "pre-audit:regulation"}
    communes = {"financement_projet", "choisir_installateur", "garanties_travaux"}
    for i, m in env.items():
        assert communes <= set(m["fiches_kb"]) and m["fiches_kb"][0].startswith("action_")
        assert ("urbanisme_assurance" in m["fiches_kb"]) == (i in ("isolation-murs", "fenetres"))
    assert {i: m.get("categorie_cil") for i, m in env.items()} == {
        "isolation-combles": "isolation_toiture", "isolation-murs": "isolation_murs",
        "isolation-plancher": "planchers_bas", "fenetres": "parois_vitrees_portes", "ventilation": None,
        "regulation-chauffage": "chauffage_froid_ecs"}
    assert env["ventilation"]["equipements_crees"] == [
        {"categorie": "ventilation", "type": "VMC_double", "origine_fiche": "ventilation"}]
    assert all(not m["equipements_crees"] for i, m in env.items() if i != "ventilation")


@pytest.mark.parametrize("modele_id", ENVELOPPE)
def test_chaque_modele_enveloppe_masque_si_sa_fiche_manque(modele_id):
    m = next(x for x in MODELES if x["id"] == modele_id)
    assert modele_id in visibles()
    assert modele_id not in visibles(sources=SOURCES_KB - {m["fiches_kb"][0]})


def test_mention_du_locataire_sur_la_regulation_seulement():
    reg = next(m for m in MODELES if m["id"] == "regulation-chauffage")
    loc, proprio = maison(statut="locataire"), maison()
    assert pj.mention(reg, parcours(loc)) == "Les travaux sur le chauffage se décident avec votre propriétaire."
    assert pj.mention(reg, parcours(proprio)) is None
    assert all(pj.mention(m, parcours(loc)) is None for m in MODELES if m["id"] != "regulation-chauffage")


def test_lier_les_combles_recopie_l_action_telle_quelle():
    combles = {"action": "isolation_combles", "cout_eur": {"bas": 2730, "haut": 6370},
               "economie_annuelle_eur": {"bas": 255, "haut": 345, "central": 300},
               "statuts": {"cout_eur": "suppose", "economie_annuelle_eur": "calcule"}, "horizon": "maintenant"}
    r = pj.depuis_audit({"priorites": [combles]}, "isolation_combles", LE_12_10, "a1")
    assert (r["budget_bas_eur"], r["budget_haut_eur"], r["economie_annuelle_eur"]) == (2730, 6370, 300)
    assert (r["budget_statut"], r["economie_statut"], r["budget_date"]) == ("suppose", "calcule", "2026-10-12")


@pytest.mark.parametrize("modif, motif", [
    ({"categorie_cil": "toiture"}, "categorie_cil"),
    ({"mention_locataire": "oui"}, "mention_locataire"),
    ({"outil": "pre-audit:isolation_toit"}, "action du pré-audit inconnue"),
])
def test_les_nouveaux_champs_sont_verifies(tmp_path, modif, motif):
    m = {**next(x for x in MODELES if x["id"] == "isolation-combles"), **modif}
    f = tmp_path / "m.json"
    f.write_text(json.dumps({"modeles": [m]}), encoding="utf-8")
    with pytest.raises(pj.ModeleInvalide, match=motif):
        pj.charger_modeles(f)
