"""Moteur d'entretien (carnet, lot 3) — sur la table d'EXEMPLE, jamais sur la vraie table."""

import json
from datetime import date
from pathlib import Path

import pytest

from app.services.entretien import (
    CHEMIN_TABLE, TacheInvalide, ajouter_mois, charger_table, charger_taches, echeances,
    reporter_au_mois_prefere, verifications,
)

EXEMPLE = Path(__file__).parent / "fixtures" / "entretien_exemple.json"
TACHES = charger_taches(EXEMPLE, strict=True)
PAR_ID = {t["id"]: t for t in TACHES}


def _eq(id_="eq", categorie="chauffage", type_="PAC_air_eau", date_pose=None, annee_pose=None,
        en_service=True, puissance=None, unite=None):
    return {"id": id_, "categorie": categorie, "type": type_, "date_pose": date_pose, "annee_pose": annee_pose,
            "en_service": en_service, "puissance": puissance, "unite": unite}


def _une(eq, tache_id, aujourd_hui, derniers_faits=None, maison=None):
    lignes = [l for l in echeances([eq] if eq else [], [PAR_ID[tache_id]], derniers_faits or {}, aujourd_hui, maison)]
    assert len(lignes) <= 1
    return lignes[0] if lignes else None


def _table(tmp_path, *taches) -> Path:
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"version": "x", "taches": list(taches)}), encoding="utf-8")
    return p


# ---------------------------------------------------------------- chargeur

def test_la_vraie_table_se_charge_en_mode_strict():
    """La table relue par Stéphane (lot 3 bis) : 18 tâches, aucune écartée par le chargeur."""
    table = charger_table(CHEMIN_TABLE, strict=True)
    assert len(table["taches"]) == 18 and table["version"] == "2026-10-20"
    obligations = [t for t in table["taches"] if t["nature"] == "obligation"]
    assert {t["id"] for t in obligations} == {
        "chaudiere-entretien", "pac-entretien", "poele-entretien", "ramonage", "spanc-controle", "debroussaillement"}
    assert all(t["source"]["type"] == "officiel" and t["source"]["url"] for t in obligations)


def test_la_table_d_exemple_se_charge_en_mode_strict():
    assert len(TACHES) == 8


BASE = {"id": "t", "applique_a": {"categorie": "ecs", "types": []}, "libelle": "L", "frequence_mois": 12,
        "qui": "soi", "nature": "recommande", "valide_le": "2000-01-01"}
OFFICIEL = {"type": "officiel", "titre": "Texte", "url": "https://exemple.invalid"}


@pytest.mark.parametrize("modif, motif", [
    ({"nature": "obligation"}, "obligation exige"),                                  # sans source
    ({"nature": "obligation", "source": {**OFFICIEL, "type": "guide"}}, "obligation exige"),
    ({"nature": "obligation", "source": {**OFFICIEL, "url": None}}, "obligation exige"),
    ({"valide_le": None}, "relecture"),
    ({"valide_le": "20/10/2026"}, "relecture"),
    ({"applique_a": {"categorie": "ecs", "types": ["chaudiere_gaz"]}}, "type inconnu"),
    ({"applique_a": {"categorie": "piscine"}}, "categorie"),
    ({"regle": "annee_civile"}, "n_annees"),
    ({"regle": "hebdo"}, "regle"),
    ({"frequence_moi": 3}, "inconnu"),
    ({"mois_preferes": [0, 13]}, "mois"),
    ({"puissance_kw": {"min": 70, "max": 4}}, "puissance_kw"),
    ({"applique_a": {"maison": {}}, "puissance_kw": {"min": 4, "max": 70}}, "maison"),
    ({"source": {"type": "blog", "titre": "x", "url": None}}, "source"),
])
def test_une_tache_invalide_est_refusee_en_mode_strict(tmp_path, modif, motif):
    tache = {**BASE, **modif}
    tache = {k: v for k, v in tache.items() if v is not None}
    with pytest.raises(TacheInvalide, match=motif):
        charger_table(_table(tmp_path, tache), strict=True)


def test_en_production_la_tache_invalide_est_ignoree_et_journalisee(tmp_path, caplog):
    sans_relecture = {k: v for k, v in BASE.items() if k != "valide_le"}
    p = _table(tmp_path, {**BASE, "id": "bonne"}, {**sans_relecture, "id": "non-relue"})
    with caplog.at_level("WARNING", logger="helios.entretien"):
        taches = charger_taches(p)
    assert [t["id"] for t in taches] == ["bonne"]
    assert "non-relue" in caplog.text


def test_un_id_en_double_est_refuse(tmp_path):
    with pytest.raises(TacheInvalide, match="double"):
        charger_table(_table(tmp_path, BASE, BASE), strict=True)


# ------------------------------------------------------------------ règle « mois »

def test_pac_posee_le_15_03_2020_sans_journal():
    pac = _eq(date_pose=date(2020, 3, 15))
    for aujourd_hui, statut in [(date(2021, 6, 1), "plus_tard"), (date(2022, 1, 20), "bientot"),
                                (date(2022, 3, 1), "ce_mois"), (date(2022, 3, 16), "en_retard")]:
        l = _une(pac, "exemple-pac-24-mois", aujourd_hui)
        assert (l["echeance"], l["statut"], l["provenance"]) == (date(2022, 3, 15), statut, "date_pose"), aujourd_hui


def test_le_journal_prime_sur_la_date_de_pose_et_fait_avancer_l_echeance():
    pac = _eq(date_pose=date(2020, 3, 15))
    faits = {("exemple-pac-24-mois", "eq"): date(2022, 4, 2)}
    l = _une(pac, "exemple-pac-24-mois", date(2023, 1, 1), faits)
    assert (l["provenance"], l["date_reference"], l["echeance"], l["statut"]) == (
        "journal", date(2022, 4, 2), date(2024, 4, 2), "plus_tard")
    faits = {("exemple-pac-24-mois", "eq"): date(2024, 4, 2)}
    assert _une(pac, "exemple-pac-24-mois", date(2025, 1, 1), faits)["echeance"] == date(2026, 4, 2)


def test_annee_seule_reference_supposee_au_1er_juillet():
    l = _une(_eq(annee_pose=2021), "exemple-pac-24-mois", date(2023, 1, 1))
    assert (l["date_reference"], l["provenance"], l["reference_supposee"], l["echeance"]) == (
        date(2021, 7, 1), "annee_pose", True, date(2023, 7, 1))


def test_ni_date_ni_annee_a_planifier():
    l = _une(_eq(), "exemple-pac-24-mois", date(2026, 10, 21))
    assert (l["date_reference"], l["provenance"], l["echeance"], l["statut"]) == (None, "inconnue", None, "a_planifier")


def test_ajout_de_mois_en_fin_de_mois():
    assert ajouter_mois(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert ajouter_mois(date(2023, 1, 31), 1) == date(2023, 2, 28)
    assert ajouter_mois(date(2025, 11, 15), 3) == date(2026, 2, 15)


# --------------------------------------------------------------- mois préférés

def test_report_au_mois_prefere_y_compris_d_une_annee_a_l_autre():
    assert reporter_au_mois_prefere(date(2025, 2, 10), [4, 5]) == date(2025, 4, 1)
    assert reporter_au_mois_prefere(date(2025, 4, 20), [4, 5]) == date(2025, 4, 20)  # déjà dans un mois préféré
    assert reporter_au_mois_prefere(date(2025, 7, 3), [4, 5]) == date(2026, 4, 1)    # passe l'année
    assert reporter_au_mois_prefere(date(2025, 12, 5), [1]) == date(2026, 1, 1)


def test_mois_preferes_appliques_a_une_tache_mois():
    clim = _eq(categorie="clim", type_="split", date_pose=date(2024, 8, 10))
    l = _une(clim, "exemple-clim-printemps", date(2025, 1, 1))
    assert l["echeance"] == date(2026, 4, 1)  # 10/08/2025 calculé → avril suivant
    assert l["periode_conseillee"] is None


# --------------------------------------------------------------- année civile

def test_annee_civile_limite_au_31_decembre_et_mois_non_deplaces():
    chaudiere = _eq(type_="chaudiere_gaz", date_pose=date(2019, 11, 2))
    faits = {("exemple-chaudiere-annee-civile", "eq"): date(2025, 5, 14)}
    l = _une(chaudiere, "exemple-chaudiere-annee-civile", date(2026, 1, 10), faits)
    # Fait en mai 2025 → le suivant avant le 31/12/2026, pas avant mai 2026.
    assert (l["echeance"], l["statut"], l["periode_conseillee"]) == (date(2026, 12, 31), "plus_tard", [9, 10])
    assert _une(chaudiere, "exemple-chaudiere-annee-civile", date(2026, 12, 15), faits)["statut"] == "ce_mois"
    # Premier entretien : même calcul depuis la pose.
    assert _une(chaudiere, "exemple-chaudiere-annee-civile", date(2020, 3, 1))["echeance"] == date(2020, 12, 31)


# ------------------------------------------------------------------- puissance

def test_puissance_hors_plage_absente_inconnue_avec_mention():
    t = "exemple-chaudiere-annee-civile"
    auj = date(2026, 10, 21)
    assert _une(_eq(type_="chaudiere_gaz", annee_pose=2015, puissance=24, unite="kW"), t, auj)["mention_puissance"] is None
    assert _une(_eq(type_="chaudiere_gaz", annee_pose=2015, puissance=3, unite="kW"), t, auj) is None
    assert _une(_eq(type_="chaudiere_gaz", annee_pose=2015, puissance=450, unite="kW"), t, auj) is None
    inconnue = _une(_eq(type_="chaudiere_gaz", annee_pose=2015), t, auj)
    assert inconnue["mention_puissance"] == "Obligatoire si la puissance est entre 4 et 400 kW : vérifiez sur la plaque."
    # Une puissance dans une autre unité ne se compare pas : elle compte comme inconnue.
    assert _une(_eq(type_="chaudiere_gaz", annee_pose=2015, puissance=200, unite="L"), t, auj)["mention_puissance"]


# --------------------------------------------------------- mois actifs, catégories

def test_mois_actifs_masquent_la_tache_hors_saison():
    clim = _eq(categorie="clim", type_="split", date_pose=date(2024, 6, 1))
    assert _une(clim, "exemple-clim-ete-seulement", date(2025, 7, 15)) is not None
    assert _une(clim, "exemple-clim-ete-seulement", date(2025, 11, 15)) is None


def test_categorie_en_liste_et_types_vides():
    pac_air_air = _eq(categorie="chauffage", type_="PAC_air_air", annee_pose=2020)
    assert _une(pac_air_air, "exemple-clim-printemps", date(2025, 1, 1)) is not None
    for type_ in ("VMC_simple", "VMC_double", "autre"):
        assert _une(_eq(categorie="ventilation", type_=type_), "exemple-vmc-toute-categorie", date(2025, 1, 1))
    assert _une(_eq(categorie="ecs", type_="ballon_elec"), "exemple-vmc-toute-categorie", date(2025, 1, 1)) is None


def test_un_equipement_hors_service_ne_produit_rien():
    deposes = [_eq(id_=f"e{i}", categorie=c, type_=t, annee_pose=2015, en_service=False)
               for i, (c, t) in enumerate([("chauffage", "PAC_air_eau"), ("clim", "split"), ("ventilation", "VMC_simple")])]
    assert [l for l in echeances(deposes, TACHES, {}, date(2025, 7, 1)) if l["equipement_id"]] == []


# ------------------------------------------------------------- tâches de maison

def test_taches_de_maison_sans_equipement():
    auj = date(2026, 10, 21)
    l = _une(None, "exemple-maison", auj, maison={"type_logement": "appartement"})
    assert (l["equipement_id"], l["statut"]) == (None, "a_planifier")
    faits = {("exemple-maison", None): date(2026, 6, 1)}
    assert _une(None, "exemple-maison", auj, faits, maison={})["echeance"] == date(2026, 12, 1)


def test_tache_de_maison_sous_condition_de_fiche():
    auj = date(2026, 10, 21)
    assert _une(None, "exemple-maison-sous-condition", auj, maison={"type_logement": "maison"}) is not None
    assert _une(None, "exemple-maison-sous-condition", auj, maison={"type_logement": "appartement"}) is None
    # Un champ que la fiche n'a pas (zone_old avant le lot 3 bis) : tâche absente.
    assert _une(None, "exemple-maison-sous-condition", auj, maison={}) is None
    assert _une(None, "exemple-maison-sous-condition", auj, maison=None) is None


# ------------------------------------------------------------------------- tri

def test_tri_statut_puis_date_puis_obligation():
    auj = date(2026, 10, 21)
    equipements = [
        _eq(id_="pac", date_pose=date(2024, 11, 1)),                       # échéance 01/11/2026 : ce mois
        _eq(id_="chaudiere", type_="chaudiere_gaz", date_pose=date(2025, 3, 1),
            puissance=24, unite="kW"),                                     # 31/12/2026 : bientôt, obligation
        _eq(id_="vmc", categorie="ventilation", type_="VMC_simple", date_pose=date(2026, 4, 1)),  # 01/10 : retard
        _eq(id_="vmc2", categorie="ventilation", type_="VMC_double"),     # à planifier
        _eq(id_="clim", categorie="clim", type_="split", date_pose=date(2026, 9, 1)),  # avril 2027 : plus tard
    ]
    lignes = echeances(equipements, TACHES, {}, auj, maison={"type_logement": "maison"})
    statuts = [l["statut"] for l in lignes]
    rang = {"en_retard": 0, "ce_mois": 1, "bientot": 2, "a_planifier": 3, "plus_tard": 4}
    assert statuts == sorted(statuts, key=rang.get)
    assert [l["equipement_id"] or l["tache_id"] for l in lignes] == [
        "vmc", "pac", "chaudiere",
        # À planifier : l'obligation d'abord, puis les deux recommandations départagées par libellé.
        "exemple-maison-sous-condition", "vmc2", "exemple-maison",
        "clim",
    ]


# ------------------------------------------------------------- zone de débroussaillement

def test_zone_old_oui_non_ne_sais_pas():
    auj = date(2026, 10, 21)
    t = "exemple-maison-zone"
    maison = {"type_logement": "maison"}
    assert _une(None, t, auj, maison={**maison, "zone_old": "oui"})["nature"] == "obligation"
    assert _une(None, t, auj, maison={**maison, "zone_old": "non"}) is None
    assert _une(None, t, auj, maison={**maison, "zone_old": "ne_sais_pas"}) is None
    v = verifications(TACHES, {**maison, "zone_old": "ne_sais_pas"})
    assert v == [{"tache_id": t, "champ": "zone_old", "libelle": "Vérifiez si votre terrain est concerné",
                  "tache_libelle": PAR_ID[t]["libelle"], "nature": "obligation", "lien": "https://exemple.invalid/zone"}]
    assert verifications(TACHES, {**maison, "zone_old": "oui"}) == []
    assert verifications(TACHES, {**maison, "zone_old": "non"}) == []


def test_zone_old_jamais_pour_un_appartement_ni_un_type_inconnu():
    auj = date(2026, 10, 21)
    for type_logement in ("appartement", None):
        fiche = {"type_logement": type_logement, "zone_old": "oui"}
        assert _une(None, "exemple-maison-zone", auj, maison=fiche) is None
        assert verifications(TACHES, {**fiche, "zone_old": "ne_sais_pas"}) == []
