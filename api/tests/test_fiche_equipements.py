"""Carnet, lot 7 : la correspondance équipement → fiche Maison, en fonctions pures.

Sans base. Les équipements et la maison sont des dictionnaires : `_champ` les lit comme
des modèles SQLAlchemy, c'est ce qui rend ces fonctions testables à ce prix.

Le test de couverture est le plus important du module : il interdit qu'un type
d'équipement reste sans traduction, ou qu'une traduction sorte une valeur que
`schemas/house.py` refuserait.
"""
from datetime import date
from typing import get_args

import pytest

from app.models.equipement import ORIGINES_FICHE, TYPES_PAR_CATEGORIE
from app.schemas.house import Chauffage, Ecs, Ventilation
from app.services import fiche_equipements as fe


def eq(origine, categorie, type_, **kw) -> dict:
    defauts = dict(origine_fiche=origine, categorie=categorie, type=type_, en_service=True,
                   date_pose=None, annee_pose=None)
    defauts.update(kw)
    return defauts


# — La table de correspondance couvre tout, et ne sort rien d'invalide —

def test_chaque_origine_connait_ses_champs():
    assert set(fe.CHAMPS_PAR_ORIGINE) == set(ORIGINES_FICHE)


@pytest.mark.parametrize("origine,categorie", [
    ("chauffage_principal", "chauffage"), ("chauffage_appoint", "chauffage"),
    ("ecs", "ecs"), ("clim", "clim"), ("ventilation", "ventilation"),
])
def test_tous_les_types_sont_traduits(origine, categorie):
    """Un type absent de la table remonterait `None` : la fiche resterait silencieusement
    libre alors que le foyer a bel et bien un appareil."""
    table = fe._VERS_FICHE["clim" if origine == "clim" else categorie]
    assert set(table) == set(TYPES_PAR_CATEGORIE[categorie])


@pytest.mark.parametrize("origine,categorie,literal", [
    ("chauffage_principal", "chauffage", Chauffage), ("chauffage_appoint", "chauffage", Chauffage),
    ("ecs", "ecs", Ecs), ("ventilation", "ventilation", Ventilation),
])
def test_aucune_valeur_inventee(origine, categorie, literal):
    permises = set(get_args(literal))
    for type_ in TYPES_PAR_CATEGORIE[categorie]:
        valeur = fe.valeur_fiche(origine, categorie, type_)
        assert valeur is None or valeur in permises, f"{type_} → {valeur}"


def test_clim_ecrit_un_libelle_assez_court():
    # `clim_type` est un texte libre borné à 50 caractères (`schemas/house.py`).
    for type_ in TYPES_PAR_CATEGORIE["clim"]:
        assert len(fe.valeur_fiche("clim", "clim", type_)) <= 50


# — Ce qu'un équipement impose à la fiche —

def test_chauffage_impose_son_code_et_son_annee():
    assert fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee_pose=2016)) == {
        "chauffage_principal": "gaz", "chauffage_principal_annee": 2016}


def test_la_date_exacte_prime_sur_lannee_declaree():
    champs = fe.champs_fiche_depuis(eq("ecs", "ecs", "thermodynamique",
                                      date_pose=date(2021, 3, 4), annee_pose=1999))
    assert champs == {"ecs": "thermodynamique", "ecs_annee": 2021}


def test_plusieurs_appareils_tombent_sur_le_meme_code():
    for type_ in ("poele_bois", "poele_granules", "insert", "chaudiere_bois"):
        champs = fe.champs_fiche_depuis(eq("chauffage_appoint", "chauffage", type_))
        assert champs["chauffage_appoint"] == "bois"


def test_la_clim_pose_le_booleen_et_le_libelle_sans_annee():
    champs = fe.champs_fiche_depuis(eq("clim", "clim", "gainable", annee_pose=2019))
    assert champs == {"clim": True, "clim_type": "Gainable"}
    assert "clim_nb_pieces" not in champs  # il reste au foyer


def test_un_equipement_sans_date_vide_lannee_de_la_fiche():
    """Règle STRICTE après la migration : c'est l'équipement qui dit la vérité."""
    champs = fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "convecteurs"))
    assert champs == {"chauffage_principal": "elec_direct", "chauffage_principal_annee": None}


@pytest.mark.parametrize("equipement", [
    eq("chauffage_principal", "chauffage", "chaudiere_gaz", en_service=False),
    eq(None, "chauffage", "chaudiere_gaz"),
    eq("ecs", "ecs", "autre"),          # décision 3 : pas d'équivalent dans la fiche
    eq("ventilation", "ventilation", "autre"),
])
def test_nimpose_rien(equipement):
    assert fe.champs_fiche_depuis(equipement) == {}


# — Les verrous —

def test_un_type_sans_equivalent_ne_verrouille_pas():
    """Décision 3 : le foyer peut avoir une autre solution que celles que le carnet nomme."""
    assert fe.champs_verrouilles([eq("ecs", "ecs", "autre")]) == []
    assert fe.champs_verrouilles([eq("ventilation", "ventilation", "autre")]) == []


def test_les_verrous_couvrent_les_champs_de_lorigine():
    equipements = [eq("chauffage_principal", "chauffage", "PAC_air_eau"), eq("clim", "clim", "split")]
    assert set(fe.champs_verrouilles(equipements)) == {
        "chauffage_principal", "chauffage_principal_annee", "clim", "clim_type"}


def test_un_ancien_equipement_ne_verrouille_rien():
    assert fe.champs_verrouilles([eq("ecs", "ecs", "ballon_elec", en_service=False)]) == []


def test_le_reseau_de_chaleur_est_verrouille_malgre_labsence_decart():
    """Décision 1 : rien à réécrire, mais la fiche ne peut plus contredire l'appareil."""
    equipements = [eq("chauffage_principal", "chauffage", "autre", annee_pose=2010)]
    assert "chauffage_principal" in fe.champs_verrouilles(equipements)


# — Les écarts —

def test_ecart_sur_le_type_et_sur_lannee():
    maison = {"chauffage_principal": "fioul", "chauffage_principal_annee": 1998}
    trouves = fe.ecarts(maison, [eq("chauffage_principal", "chauffage", "PAC_air_eau", annee_pose=2016)])
    assert {e["champ"]: (e["valeur_fiche"], e["valeur_equipement"]) for e in trouves} == {
        "chauffage_principal": ("fioul", "PAC_air_eau"),
        "chauffage_principal_annee": (1998, 2016),
    }


def test_aucun_ecart_quand_la_fiche_est_juste():
    maison = {"ecs": "solaire", "ecs_annee": 2020}
    assert fe.ecarts(maison, [eq("ecs", "ecs", "solaire", annee_pose=2020)]) == []


@pytest.mark.parametrize("valeur_fiche", ["reseau", "autre"])
def test_le_reseau_de_chaleur_nest_pas_un_ecart(valeur_fiche):
    maison = {"chauffage_principal": valeur_fiche, "chauffage_principal_annee": 2010}
    assert fe.ecarts(maison, [eq("chauffage_principal", "chauffage", "autre", annee_pose=2010)]) == []


def test_un_autre_chauffage_corrige_une_fiche_qui_dit_autre_chose():
    maison = {"chauffage_principal": "gaz", "chauffage_principal_annee": 2010}
    trouves = fe.ecarts(maison, [eq("chauffage_principal", "chauffage", "autre", annee_pose=2010)])
    assert [e["champ"] for e in trouves] == ["chauffage_principal"]


def test_la_clim_du_carnet_corrige_une_fiche_muette():
    maison = {"clim": False, "clim_type": None}
    trouves = fe.ecarts(maison, [eq("clim", "clim", "multisplit")])
    assert {e["champ"] for e in trouves} == {"clim", "clim_type"}


# — Vider —

def test_vider_une_origine():
    assert fe.champs_a_vider("chauffage_principal") == {
        "chauffage_principal": None, "chauffage_principal_annee": None}
    assert fe.champs_a_vider("ventilation") == {"ventilation": None}


def test_vider_la_clim_la_declare_absente_sans_toucher_au_nombre_de_pieces():
    champs = fe.champs_a_vider("clim")
    assert champs == {"clim": False, "clim_type": None}
    assert "clim_nb_pieces" not in champs
