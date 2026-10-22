"""Carnet, lot 7 : la correspondance équipement → fiche Maison, en fonctions pures.

Sans base : des objets jetables portent les mêmes attributs que les modèles.

Le test de couverture est le plus important du module — il interdit qu'une traduction
sorte une valeur que `schemas/house.py` refuserait, et qu'un type d'équipement reçoive
une traduction inventée.
"""
import uuid
from datetime import date
from types import SimpleNamespace
from typing import get_args

import pytest

from app.models.equipement import ORIGINES_FICHE, TYPES_PAR_CATEGORIE
from app.schemas.house import Chauffage, Ecs, Ventilation
from app.services import fiche_equipements as fe

AUJOURD_HUI = date(2026, 10, 22)

# Tous les champs de fiche que le lot touche, pour que `getattr` ne mente jamais.
_CHAMPS_FICHE = dict.fromkeys(fe.LIBELLES_CHAMPS, None) | {"clim_nb_pieces": None}


def eq(origine, categorie, type_, **kw):
    champs = dict(id=uuid.uuid4(), origine_fiche=origine, categorie=categorie, type=type_,
                  en_service=True, date_pose=None, annee_pose=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def maison(**kw):
    return SimpleNamespace(**(_CHAMPS_FICHE | kw))


# — La table de correspondance couvre tout, et ne sort rien d'invalide —

def test_chaque_origine_de_la_fiche_est_connue():
    assert set(fe.ORIGINES) == set(ORIGINES_FICHE)


@pytest.mark.parametrize("categorie,literal", [
    ("chauffage", Chauffage), ("ecs", Ecs), ("ventilation", Ventilation),
])
def test_aucune_valeur_de_fiche_inventee(categorie, literal):
    permises = set(get_args(literal))
    for type_, acceptees in fe._TYPE_VERS_FICHE[categorie].items():
        assert type_ in TYPES_PAR_CATEGORIE[categorie], type_
        assert set(acceptees) <= permises, f"{type_} → {acceptees}"


@pytest.mark.parametrize("categorie", ["chauffage", "ecs", "ventilation"])
def test_les_seuls_types_sans_equivalent_sont_des_autres(categorie):
    """Un type oublié laisserait la fiche libre en silence, alors que le foyer a un appareil."""
    manquants = set(TYPES_PAR_CATEGORIE[categorie]) - set(fe._TYPE_VERS_FICHE[categorie])
    assert manquants <= {"autre"}


def test_les_libelles_de_clim_sont_des_types_connus_et_tiennent_dans_la_fiche():
    # `clim_type` est un texte libre borné à 50 caractères (`schemas/house.py`).
    assert set(fe.LIBELLES_CLIM) <= set(TYPES_PAR_CATEGORIE["clim"])
    assert all(len(v) <= 50 for v in fe.LIBELLES_CLIM.values())


def test_le_sens_inverse_retombe_sur_les_memes_codes():
    """`FICHE_VERS_TYPE` sert les suggestions du lot 1 : un aller-retour ne doit pas dériver."""
    for code_fiche, type_eq in fe.FICHE_VERS_TYPE.items():
        assert code_fiche in fe._TYPE_VERS_FICHE["chauffage"].get(type_eq, ())


# — Ce qu'un équipement fixe dans la fiche —

def test_le_chauffage_fixe_son_code_et_son_annee():
    assert fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee_pose=2016)) == {
        "chauffage_principal": "gaz", "chauffage_principal_annee": 2016}


def test_la_date_exacte_prime_sur_lannee_declaree():
    champs = fe.champs_fiche_depuis(eq("ecs", "ecs", "thermodynamique",
                                       date_pose=date(2021, 3, 4), annee_pose=1999))
    assert champs == {"ecs": "thermodynamique", "ecs_annee": 2021}


@pytest.mark.parametrize("type_", ["poele_bois", "poele_granules", "insert", "chaudiere_bois"])
def test_plusieurs_appareils_tombent_sur_le_meme_code(type_):
    assert fe.champs_fiche_depuis(eq("chauffage_appoint", "chauffage", type_))["chauffage_appoint"] == "bois"


def test_la_clim_pose_le_booleen_et_le_libelle_sans_annee():
    champs = fe.champs_fiche_depuis(eq("clim", "clim", "gainable", annee_pose=2019))
    assert champs == {"clim": True, "clim_type": "Gainable"}
    # La fiche n'a pas d'année de clim, et le nombre de pièces reste au foyer.
    assert "clim_nb_pieces" not in champs


def test_une_clim_autre_ne_fixe_que_sa_presence():
    assert fe.champs_fiche_depuis(eq("clim", "clim", "autre")) == {"clim": True}


def test_un_equipement_sans_date_vide_lannee_de_la_fiche():
    """Règle STRICTE après la reprise : l'équipement gagne aussi quand il se tait."""
    assert fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "convecteurs")) == {
        "chauffage_principal": "elec_direct", "chauffage_principal_annee": None}


@pytest.mark.parametrize("equipement", [
    eq(None, "chauffage", "chaudiere_gaz"),
    eq("ecs", "ecs", "autre"),                     # décision 3 : pas d'équivalent dans la fiche
    eq("ventilation", "ventilation", "autre"),
    eq("ecs", "chauffage", "chaudiere_gaz"),       # origine et catégorie incohérentes
])
def test_ne_fixe_rien(equipement):
    assert fe.champs_fiche_depuis(equipement) == {}


def test_un_reseau_de_chaleur_nest_pas_ecrase_par_un_autre():
    """Décision 1 : « reseau » se traduit déjà en « autre », il n'y a rien à corriger."""
    champs = fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "autre", annee_pose=2010),
                                    maison(chauffage_principal="reseau"))
    assert champs["chauffage_principal"] == "reseau"


def test_un_autre_chauffage_corrige_une_fiche_qui_dit_autre_chose():
    champs = fe.champs_fiche_depuis(eq("chauffage_principal", "chauffage", "autre"),
                                    maison(chauffage_principal="gaz"))
    assert champs["chauffage_principal"] == "autre"


# — Les verrous —

@pytest.mark.parametrize("equipement", [
    eq("ecs", "ecs", "autre"), eq("ventilation", "ventilation", "autre"),
])
def test_un_type_sans_equivalent_ne_verrouille_rien(equipement):
    """Décision 3 : le foyer peut avoir une autre solution que celles que le carnet nomme."""
    assert fe.champs_verrouilles([equipement]) == []


def test_une_clim_autre_laisse_son_type_libre():
    assert fe.champs_verrouilles([eq("clim", "clim", "autre")]) == ["clim"]


def test_les_verrous_couvrent_les_champs_de_lorigine():
    equipements = [eq("chauffage_principal", "chauffage", "PAC_air_eau"), eq("clim", "clim", "split")]
    assert set(fe.champs_verrouilles(equipements)) == {
        "chauffage_principal", "chauffage_principal_annee", "clim", "clim_type"}


def test_un_ancien_equipement_ne_verrouille_rien():
    assert fe.champs_verrouilles([eq("ecs", "ecs", "ballon_elec", en_service=False)]) == []


def test_le_reseau_de_chaleur_reste_verrouille_malgre_labsence_decart():
    """Décision 1 : rien à réécrire, mais la fiche ne peut plus contredire l'appareil."""
    equipements = [eq("chauffage_principal", "chauffage", "autre", annee_pose=2010)]
    assert "chauffage_principal" in fe.champs_verrouilles(equipements)
    assert fe.ecarts(maison(chauffage_principal="reseau", chauffage_principal_annee=2010),
                     equipements) == []


# — Les écarts et ce qu'il faut écrire —

def test_ecart_sur_le_type_et_sur_lannee():
    trouves = fe.ecarts(maison(chauffage_principal="fioul", chauffage_principal_annee=1998),
                        [eq("chauffage_principal", "chauffage", "PAC_air_eau", annee_pose=2016)])
    assert {e["champ"]: (e["fiche"], e["equipement"]) for e in trouves} == {
        "chauffage_principal": ("fioul", "PAC_air_eau"),
        "chauffage_principal_annee": (1998, 2016),
    }


def test_aucun_ecart_quand_la_fiche_est_deja_juste():
    assert fe.ecarts(maison(ecs="solaire", ecs_annee=2020),
                     [eq("ecs", "ecs", "solaire", annee_pose=2020)]) == []


def test_la_clim_du_carnet_corrige_une_fiche_muette():
    trouves = fe.ecarts(maison(clim=False), [eq("clim", "clim", "multisplit")])
    assert {e["champ"] for e in trouves} == {"clim", "clim_type"}


def test_a_ecrire_rend_aussi_les_valeurs_inchangees():
    equipements = [eq("ecs", "ecs", "solaire", annee_pose=2020)]
    assert fe.a_ecrire(maison(ecs="solaire", ecs_annee=2020), equipements) == {
        "ecs": "solaire", "ecs_annee": 2020}


def test_un_ancien_equipement_nimpose_plus_rien():
    assert fe.a_ecrire(maison(ecs="gaz"), [eq("ecs", "ecs", "solaire", en_service=False)]) == {}


# — Vider —

def test_vider_rend_les_champs_que_lequipement_fixait():
    assert fe.champs_a_vider(eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee_pose=2016)) == {
        "chauffage_principal": None, "chauffage_principal_annee": None}
    assert fe.champs_a_vider(eq("ventilation", "ventilation", "VMC_double")) == {"ventilation": None}


def test_vider_ne_touche_pas_un_champ_quil_ne_fixait_pas():
    assert fe.champs_a_vider(eq("ecs", "ecs", "autre")) == {}
    assert "clim_nb_pieces" not in fe.champs_a_vider(eq("clim", "clim", "split"))


# — Le refus d'un PATCH sur un champ verrouillé —

def test_renvoyer_la_meme_valeur_est_permis():
    """`saveBlock` de `FicheMaison.tsx` renvoie TOUT le bloc, champs verrouillés compris."""
    equipements = [eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee_pose=2016)]
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016, regulation="thermostat")
    assert fe.refus_patch(m, equipements, {"chauffage_principal": "gaz",
                                           "chauffage_principal_annee": 2016,
                                           "regulation": "connecte"}) == []


def test_changer_un_champ_verrouille_est_refuse():
    equipements = [eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee_pose=2016)]
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016)
    assert fe.refus_patch(m, equipements, {"chauffage_principal": "fioul"}) == ["chauffage_principal"]
    assert fe.refus_patch(m, equipements, {"chauffage_principal_annee": None}) == ["chauffage_principal_annee"]


def test_un_champ_libre_passe_toujours():
    equipements = [eq("clim", "clim", "split")]
    m = maison(clim=True, clim_type="Split", clim_nb_pieces=2)
    assert fe.refus_patch(m, equipements, {"clim_nb_pieces": 4, "ecs": "ballon_elec"}) == []


# — La reprise des données existantes (migration 0030) —

def test_la_reprise_recopie_lannee_de_la_fiche_dans_un_equipement_sans_date():
    """Décision 2 : à la reprise SEULEMENT, l'équipement muet hérite de l'année de la fiche."""
    e = eq("chauffage_principal", "chauffage", "chaudiere_gaz")
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016)
    plan = fe.reprise(m, [e], AUJOURD_HUI)
    assert plan["annees"] == {e.id: 2016}
    assert plan["fiche"] == {}  # l'année reprise referme l'écart
    assert len(plan["journal"]) == 1
    assert plan["journal"][0]["titre"] == "Fiche mise à jour depuis le carnet"
    assert "2016" in plan["journal"][0]["note"]


def test_la_reprise_fait_gagner_lequipement_et_consigne_lancienne_valeur():
    e = eq("chauffage_principal", "chauffage", "PAC_air_eau", annee_pose=2021)
    plan = fe.reprise(maison(chauffage_principal="fioul", chauffage_principal_annee=1998),
                      [e], AUJOURD_HUI)
    assert plan["annees"] == {}
    assert plan["fiche"] == {"chauffage_principal": "PAC_air_eau", "chauffage_principal_annee": 2021}
    assert len(plan["journal"]) == 1
    note = plan["journal"][0]["note"]
    assert "fioul" in note and "1998" in note
    assert plan["journal"][0]["equipement_id"] == e.id
    assert plan["journal"][0]["type"] == "autre"


def test_la_reprise_ne_trouve_rien_quand_tout_concorde():
    """Idempotence : relancée après elle-même, elle n'a plus rien à faire."""
    e = eq("ecs", "ecs", "solaire", annee_pose=2020)
    plan = fe.reprise(maison(ecs="solaire", ecs_annee=2020), [e], AUJOURD_HUI)
    assert plan == {"annees": {}, "fiche": {}, "journal": []}


def test_la_reprise_est_idempotente_sur_un_vrai_ecart():
    e = eq("ecs", "ecs", "thermodynamique", annee_pose=2022)
    m = maison(ecs="ballon_elec", ecs_annee=2005)
    premier = fe.reprise(m, [e], AUJOURD_HUI)
    for champ, valeur in premier["fiche"].items():
        setattr(m, champ, valeur)
    assert fe.reprise(m, [e], AUJOURD_HUI) == {"annees": {}, "fiche": {}, "journal": []}


def test_la_reprise_ne_date_pas_un_equipement_sans_equivalent():
    """Une eau chaude « autre » n'écrit rien : son année n'a pas à venir de la fiche."""
    e = eq("ecs", "ecs", "autre")
    plan = fe.reprise(maison(ecs="ballon_elec", ecs_annee=2005), [e], AUJOURD_HUI)
    assert plan == {"annees": {}, "fiche": {}, "journal": []}
    assert e.annee_pose is None


def test_la_reprise_ignore_les_anciens_equipements():
    e = eq("ecs", "ecs", "solaire", en_service=False)
    plan = fe.reprise(maison(ecs="ballon_elec", ecs_annee=2005), [e], AUJOURD_HUI)
    assert plan == {"annees": {}, "fiche": {}, "journal": []}


def test_la_reprise_groupe_les_champs_dun_meme_equipement_en_une_entree():
    e = eq("clim", "clim", "split")
    plan = fe.reprise(maison(clim=False, clim_type=None), [e], AUJOURD_HUI)
    assert plan["fiche"] == {"clim": True, "clim_type": "Split"}
    assert len(plan["journal"]) == 1
    assert "vide" in plan["journal"][0]["note"]
