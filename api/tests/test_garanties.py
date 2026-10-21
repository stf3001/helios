"""Garanties de chantier, âge des équipements et suggestions de la fiche — sans base."""

from datetime import date, timedelta
from types import SimpleNamespace

from app.services.garanties import (
    age_ans, fin_garanties_chantier, garanties_maison, statut_garantie,
)
from app.services.suggestions_fiche import suggestions


def _fins(reception):
    return {g["code"]: g["fin"] for g in fin_garanties_chantier(reception)}


def test_trois_garanties_depuis_la_reception():
    assert _fins(date(2025, 3, 15)) == {
        "parfait_achevement": date(2026, 3, 15),
        "bon_fonctionnement": date(2027, 3, 15),
        "decennale": date(2035, 3, 15),
    }


def test_un_29_fevrier_tombe_au_28_les_annees_non_bissextiles():
    assert _fins(date(2024, 2, 29)) == {
        "parfait_achevement": date(2025, 2, 28),
        "bon_fonctionnement": date(2026, 2, 28),
        "decennale": date(2034, 2, 28),
    }


def test_statuts_autour_du_seuil_de_60_jours():
    fin = date(2026, 12, 31)
    assert statut_garantie(fin, fin - timedelta(days=61)) == "en_cours"
    assert statut_garantie(fin, fin - timedelta(days=60)) == "bientot"
    assert statut_garantie(fin, fin) == "bientot"  # couverte jusqu'au dernier jour
    assert statut_garantie(fin, fin + timedelta(days=1)) == "expiree"


def test_une_annee_seule_donne_une_date_supposee_au_1er_juillet():
    eq = {"date_pose": None, "annee_pose": 2014}
    assert age_ans(eq, date(2026, 6, 30)) == (11, "suppose")
    assert age_ans(eq, date(2026, 7, 1)) == (12, "suppose")


def test_une_date_exacte_donne_un_age_calcule():
    assert age_ans({"date_pose": date(2016, 10, 22), "annee_pose": 1990}, date(2026, 10, 21)) == (9, "calcule")
    assert age_ans({"date_pose": None, "annee_pose": None}, date(2026, 10, 21)) == (None, None)


def test_garanties_triees_par_fin_et_hors_service_exclu():
    auj = date(2026, 10, 21)
    travaux = [{"id": "t1", "nature": "Isolation des combles", "date_reception": date(2025, 3, 15)},
               {"id": "t2", "nature": "Sans réception", "date_reception": None}]
    equipements = [
        {"id": "e1", "type": "PAC_air_eau", "marque": "Atlantic", "modele": None, "en_service": True,
         "garantie_fabricant_fin": date(2026, 11, 30), "date_pose": None, "annee_pose": 2021},
        {"id": "e2", "type": "ballon_elec", "marque": None, "modele": None, "en_service": False,
         "garantie_fabricant_fin": date(2030, 1, 1), "date_pose": None, "annee_pose": None},
    ]
    liste = garanties_maison(equipements, travaux, auj)
    assert [g["fin"] for g in liste] == sorted(g["fin"] for g in liste)
    assert [(g["provenance"], g["code"]) for g in liste] == [
        ("travaux", "parfait_achevement"),   # 15/03/2026, expirée
        ("equipement", "fabricant"),         # 30/11/2026, dans 40 jours
        ("travaux", "bon_fonctionnement"),   # 15/03/2027
        ("travaux", "decennale"),            # 15/03/2035
    ]
    assert [g["statut"] for g in liste] == ["expiree", "bientot", "en_cours", "en_cours"]
    assert all(g["mention"] for g in liste if g["provenance"] == "travaux")
    assert liste[1]["donnees"] == "declare" and liste[0]["donnees"] == "calcule"


def _maison(**kw):
    champs = dict(chauffage_principal=None, chauffage_principal_annee=None, chauffage_appoint=None,
                  chauffage_appoint_annee=None, ecs=None, ecs_annee=None, clim=None, clim_type=None,
                  ventilation=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def test_deux_suggestions_puis_une_seule_apres_creation():
    maison = _maison(chauffage_principal="PAC_air_eau", chauffage_principal_annee=2016,
                     ecs="ballon_elec", ecs_annee=2010)
    avant = suggestions(maison, [])
    assert [(s["origine_fiche"], s["categorie"], s["type"], s["annee_pose"]) for s in avant] == [
        ("chauffage_principal", "chauffage", "PAC_air_eau", 2016),
        ("ecs", "ecs", "ballon_elec", 2010),
    ]
    cree = SimpleNamespace(origine_fiche="chauffage_principal", en_service=True)
    assert [s["origine_fiche"] for s in suggestions(maison, [cree])] == ["ecs"]
    # Un équipement déposé ne compte plus : la suggestion revient.
    depose = SimpleNamespace(origine_fiche="chauffage_principal", en_service=False)
    assert len(suggestions(maison, [depose])) == 2


def test_les_codes_de_la_fiche_se_traduisent_dans_les_types():
    maison = _maison(chauffage_principal="gaz", chauffage_appoint="bois", clim=True,
                     ventilation="naturelle")
    par_origine = {s["origine_fiche"]: s for s in suggestions(maison, [])}
    assert par_origine["chauffage_principal"]["type"] == "chaudiere_gaz"
    assert par_origine["chauffage_appoint"]["type"] == "poele_bois"
    assert par_origine["clim"]["categorie"] == "clim"
    assert "ventilation" not in par_origine  # une ventilation naturelle n'est pas un appareil
