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

def test_les_dix_modeles_se_chargent():
    assert [m["id"] for m in MODELES] == [
        "panneaux-solaires", "batterie", "sortie-fioul-pac-air-eau", "sortie-gaz-pac-air-eau",
        "pac-air-air-convecteurs", "ballon-thermodynamique", "carport-solaire", "machine-eau-air",
        "eolienne-verticale", "jardin-hiver"]


def test_un_modele_dont_une_fiche_manque_n_est_pas_servi():
    assert pj.fiches_manquantes(next(m for m in MODELES if m["id"] == "jardin-hiver"), SOURCES_KB) == ["jardin_hiver"]
    assert "jardin-hiver" not in visibles()
    assert all(not pj.fiches_manquantes(m, SOURCES_KB) for m in MODELES if m["id"] != "jardin-hiver")
    # Une fiche retirée de la base fait disparaître ses modèles.
    assert "batterie" not in visibles(sources=SOURCES_KB - {"stockage_contrats"})


def test_le_locataire_ne_voit_pas_les_projets_lourds():
    assert visibles(maison(statut="locataire")) == ["machine-eau-air"]


def test_appartement_et_chauffage_actuel():
    assert visibles(maison(type_logement="appartement")) == [
        "pac-air-air-convecteurs", "ballon-thermodynamique", "machine-eau-air"]
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


def test_l_eau_se_rattache_sans_chiffre():
    assert pj.depuis_eau(LE_12_10, "w1") == {"etude_ref": {"type": "eau", "id": "w1", "date": "2026-10-12"}}


def test_seuls_les_equipements_coches_sont_crees():
    pv = MODELES[0]
    assert pj.equipements_a_creer(pv, [1]) == [pv["equipements_crees"][1]]
    assert pj.equipements_a_creer(pv, []) == []
    with pytest.raises(ValueError):
        pj.equipements_a_creer(pv, [5])
