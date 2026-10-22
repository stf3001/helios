"""Pré-audit v2.7 (lot 7) : la consommation de fioul, de gaz, de bois et de réseau de chaleur lue
avec son unité, et l'appoint hors relevé qui fait passer la puissance au volume (point 80).

Les sorties v2.6 de `maisons_combustible.maisons_v26()` sont enregistrées : une maison sans
relevé utilisable ne doit pas changer.
"""
import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.house import UNITES_PAR_AUTRE_ENERGIE, HouseUpdate
from app.services import audit_reference as ref
from app.services.audit_engine import run_audit
from app.services.autre_energie import kwh_autre_energie
from tests.maisons_combustible import cas, maisons_v26
from tests.test_audit_engine import AUJOURD_HUI, maison_type, reference_complete

V26 = Path(__file__).parent / "fixtures" / "audit_v26"


def audit(house) -> dict:
    return run_audit(house, aujourd_hui=AUJOURD_HUI)


# --- La conversion --------------------------------------------------------------------------

@pytest.mark.parametrize("type_, unite, qte, attendu", [
    ("fioul", "litres", 1500, 15000), ("fioul", "kwh", 15000, 15000), ("gaz", "kwh", 12000, 12000),
    ("gaz", "m3", 1100, 12100), ("bois_buches", "steres", 8, 13600), ("granules", "kg", 3000, 13800),
    ("reseau", "kwh", 9000, 9000),
])
def test_chaque_couple_type_unite(type_, unite, qte, attendu):
    assert kwh_autre_energie(type_, unite, qte) == pytest.approx(attendu)


def test_tous_les_couples_permis_ont_un_facteur():
    assert {(t, u) for t, us in UNITES_PAR_AUTRE_ENERGIE.items() for u in us} == \
        {(t, u) for t, u, _ in settings.audit_kwh_par_unite}


def test_couple_interdit_unite_absente_quantite_nulle():
    assert kwh_autre_energie("fioul", "m3", 10) is None
    assert kwh_autre_energie("gaz", None, 10) is None
    assert kwh_autre_energie("gaz", "kwh", 0) is None and kwh_autre_energie("gaz", "kwh", None) is None


def test_le_schema_refuse_un_type_ou_une_unite_hors_liste():
    for champs in ({"conso_autre_energie_type": "propane"}, {"conso_autre_energie_unite": "tonnes"}):
        with pytest.raises(ValidationError):
            HouseUpdate(**champs)


def test_la_migration_ramene_seulement_les_textes_sans_ambiguite():
    spec = importlib.util.spec_from_file_location(
        "m0043", Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0043_autre_energie_unite.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert [m.type_ramene(t) for t in ("Fioul", "fuel domestique", "Gaz de ville", "granulés", "bûches",
                                       "Réseau de chaleur")] == ["fioul", "fioul", "gaz", "granules",
                                                                  "bois_buches", "reseau"]
    assert [m.type_ramene(t) for t in ("Bois", "propane", "gaz et fioul", "", None)] == [None] * 5


# --- La même voie que l'électricité ---------------------------------------------------------

def test_fioul_1500_litres_a_la_main():
    """1 500 L × 10 = 15 000 kWh, rien de déduit (eau chaude électrique). Estimation :
    180 × 100 × 0,55 / 0,85 = 11 647 kWh ; ratio 15 000 / 11 647 = 1,29."""
    a = audit(cas("fioul_1500_litres"))
    c = a["consommation"]
    assert (c["conso_autre_energie_kwh_an"], c["conso_chauffage_declaree_kwh_an"]) == (15000, 15000)
    assert (c["conso_chauffage_retenue_kwh_an"], c["base_economies"], c["ratio_reel_theorique"]) == (15000, "declaree", 1.29)
    assert c["message_ratio"] == ref_message(1.29)
    assert c["statuts"]["conso_autre_energie_qte"] == "declare" and c["statuts"]["kwh_par_unite"] == "suppose"
    assert c["cout_chauffage_actuel_eur"] == round(15000 * 0.19)
    hyp = {h["cle"]: h["valeur"] for h in a["hypotheses"]}
    assert hyp["kwh_par_unite[litres]"] == 10 and "rien n'en est déduit" in hyp["eau_chaude_releve"]


def ref_message(ratio):
    from app.services.audit_engine import message_ratio
    return message_ratio(ratio)


def test_eau_chaude_au_gaz_deduite():
    """12 000 kWh de gaz, eau chaude au gaz, 3 occupants × 1 100 = 3 300 kWh : 8 700 de chauffage."""
    c = audit(cas("gaz_12000_kwh_ecs_gaz"))["consommation"]
    assert (c["eau_chaude_deduite_kwh_an"], c["conso_chauffage_declaree_kwh_an"]) == (3300, 8700)
    assert c["statuts"]["eau_chaude_deduite_kwh_an"] == "suppose"


def test_un_releve_d_une_autre_energie_est_ignore():
    a = audit(maison_type(chauffage_principal="gaz", conso_autre_energie_type="fioul",
                          conso_autre_energie_qte=1500, conso_autre_energie_unite="litres"))
    assert a["consommation"]["base_economies"] == "estimee"
    hyp = {h["cle"]: h["valeur"] for h in a["hypotheses"]}
    assert "ne porte pas sur l'énergie de votre chauffage" in hyp["conso_autre_energie"]


def test_sans_unite_la_quantite_ne_sert_pas():
    a = audit(cas("fioul_1500_litres", avec_unite=False))
    assert a["consommation"]["base_economies"] == "estimee"
    assert "unité" in {h["cle"]: h["valeur"] for h in a["hypotheses"]}["conso_autre_energie"]


def test_seuil_et_alerte_comme_la_voie_electrique():
    """1 000 kWh de gaz, dont 3 300 d'eau chaude : il ne reste rien → alerte, base estimée,
    mais le ratio est donné (0 / 11 000 = 0)."""
    a = audit(maison_type(chauffage_principal="gaz", ecs="gaz", nb_occupants=3, conso_autre_energie_type="gaz",
                          conso_autre_energie_qte=1000, conso_autre_energie_unite="kwh"))
    c = a["consommation"]
    assert c["base_economies"] == "estimee" and c["conso_chauffage_declaree_kwh_an"] == 0
    assert c["ratio_reel_theorique"] == 0
    assert a["alertes"] and "l'eau chaude (~3 300 kWh)" in a["alertes"][0]


# --- Point 80 -------------------------------------------------------------------------------

def test_appoint_hors_facture_le_volume_fait_reference():
    b = audit(reference_complete())["puissance"]
    assert (b["reference"], b["appoint"], b["p_reference_kw"]) == ("volume", "autre", b["p_volume_kw"])
    assert b["p_conso_kw"] == 4.2   # toujours affichée
    assert b["texte"] == ref.TEXTES_PUISSANCE["puissance_appoint"].format(
        t_base="-5", p_bas="4,2", p_haut="12,2", appoint="autre chauffage", p_volume="12,2")


def test_sans_appoint_rien_ne_change():
    b = audit(maison_type(chauffage_principal="elec_direct", conso_elec_kwh_an=12000))["puissance"]
    assert (b["reference"], b["appoint"]) == ("consommation", None)
    sans_appoint = audit(reference_complete(chauffage_appoint=None))["puissance"]
    assert sans_appoint["reference"] == "consommation"


def test_appoint_electrique_d_une_maison_au_gaz_releve():
    b = audit(maison_type(chauffage_principal="gaz", chauffage_appoint="elec_direct", conso_autre_energie_type="gaz",
                          conso_autre_energie_qte=12000, conso_autre_energie_unite="kwh"))["puissance"]
    assert b["reference"] == "volume" and b["appoint"] == "elec_direct"
    assert "Votre appoint (convecteurs électriques)" in b["texte"]


def test_appoint_de_meme_energie_n_est_pas_hors_releve():
    b = audit(maison_type(chauffage_principal="gaz", chauffage_appoint="gaz", conso_autre_energie_type="gaz",
                          conso_autre_energie_qte=12000, conso_autre_energie_unite="kwh"))["puissance"]
    assert b["reference"] == "consommation" and b["appoint"] is None


def test_la_regle_electrique_d_appoint_est_inchangee():
    """L'ancienne règle `APPOINT_HORS_FACTURE` et la nouvelle disent la même chose pour l'électricité."""
    from app.services.audit_engine import appoint_hors_facture
    for appoint in ref.ENERGIE_CHAUFFAGE:
        h = maison_type(chauffage_principal="elec_direct", chauffage_appoint=appoint)
        assert appoint_hors_facture(h, "electricite") == (appoint in ref.APPOINT_HORS_FACTURE), appoint


# --- Non-régression -------------------------------------------------------------------------

def _comparable(r: dict, sans_puissance: bool) -> dict:
    r = json.loads(json.dumps(r, ensure_ascii=False, default=str, sort_keys=True))
    r.pop("version_helios")
    if sans_puissance:
        r.pop("puissance", None)
    elif r.get("puissance"):
        r["puissance"].pop("appoint", None)
    return r


@pytest.mark.parametrize("nom", sorted(maisons_v26()))
def test_sans_releve_utilisable_la_v27_egale_la_v26(nom):
    """Les maisons enregistrées n'ont aucune unité : leur quantité ne sert pas, en v2.6 comme en
    v2.7. Seule la référence change, et seulement sa puissance : c'est le point 80."""
    h, pieces, emetteurs = maisons_v26()[nom]
    v27 = run_audit(h, aujourd_hui=AUJOURD_HUI, pieces=pieces, emetteurs=emetteurs)
    v26 = json.loads((V26 / f"{nom}.json").read_text(encoding="utf-8"))
    v26.pop("version_helios")
    assert _comparable(v27, sans_puissance=(nom == "reference")) == \
        {k: v for k, v in v26.items() if not (nom == "reference" and k == "puissance")}


@pytest.mark.parametrize("nom", ["fioul_1500_litres", "gaz_12000_kwh_ecs_gaz", "gaz_1100_m3", "bois_8_steres"])
def test_aucune_variable_non_remplie(nom):
    b = audit(cas(nom))["puissance"]
    assert b["texte"] and "{" not in b["texte"] and "{" not in (b["texte_plage"] or "")
