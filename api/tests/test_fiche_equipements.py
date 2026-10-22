"""Carnet, lot 7 : la fiche suit l'équipement relié — les fonctions pures, sans base.

Le parcours par l'API (même transaction, 409, 400 sur un champ verrouillé) est tenu par
`test_fiche_equipements_api.py`, contre la vraie base.
"""

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.models.house import House
from app.services import fiche_equipements as fe
from app.services.audit_engine import run_audit
from app.services.suggestions_fiche import suggestions

AUJOURD_HUI = date(2026, 10, 22)


def eq(origine, categorie, type_, annee=None, date_pose=None, en_service=True):
    return SimpleNamespace(id=uuid.uuid4(), origine_fiche=origine, categorie=categorie, type=type_,
                           annee_pose=annee, date_pose=date_pose, en_service=en_service)


def maison(**kw):
    champs = {c: None for c in fe.LIBELLES_CHAMPS}
    champs.update(kw)
    return SimpleNamespace(**champs)


def appliquer(m, champs):
    for c, v in champs.items():
        setattr(m, c, v)
    return m


# — Chaque origine : création, année, hors service, remplacement —

@pytest.mark.parametrize("origine,categorie,type_,remplacant,attendu", [
    ("chauffage_principal", "chauffage", "chaudiere_gaz", "PAC_air_eau",
     {"chauffage_principal": "gaz", "chauffage_principal_annee": 2015}),
    ("chauffage_appoint", "chauffage", "poele_granules", "convecteurs",
     {"chauffage_appoint": "bois", "chauffage_appoint_annee": 2015}),
    ("ecs", "ecs", "thermodynamique", "ballon_elec", {"ecs": "thermodynamique", "ecs_annee": 2015}),
    ("clim", "clim", "multisplit", "split", {"clim": True, "clim_type": "Multisplit"}),
    ("ventilation", "ventilation", "VMC_double", "VMC_simple", {"ventilation": "VMC_double"}),
])
def test_chaque_origine_suit_son_equipement(origine, categorie, type_, remplacant, attendu):
    champ_annee = fe.ORIGINES[origine]["annee"]
    e = eq(origine, categorie, type_, annee=2015)
    m = maison()
    assert fe.a_ecrire(m, [e]) == attendu
    assert fe.champs_verrouilles([e]) == list(attendu)

    # Une date exacte l'emporte sur l'année seule.
    e.date_pose = date(2018, 3, 1)
    if champ_annee:
        assert fe.a_ecrire(m, [e])[champ_annee] == 2018

    # Hors service sans remplaçant : ce qu'il fixait est vidé, plus rien n'est verrouillé.
    appliquer(m, fe.a_ecrire(m, [e]))
    assert fe.champs_a_vider(e) == dict.fromkeys(attendu)
    e.en_service = False
    appliquer(m, fe.champs_a_vider(e))
    assert all(getattr(m, c) is None for c in attendu)
    assert fe.champs_verrouilles([e]) == []

    # Le remplaçant hérite de l'origine : la fiche prend SES valeurs.
    nouveau = eq(origine, categorie, remplacant, annee=2026)
    appliquer(m, fe.a_ecrire(m, [e, nouveau]))
    assert fe.ecarts(m, [e, nouveau]) == []
    assert fe.champs_fiche_depuis(nouveau) == {c: getattr(m, c) for c in attendu}
    if champ_annee:
        assert getattr(m, champ_annee) == 2026


def test_un_equipement_sans_annee_vide_l_annee_de_la_fiche():
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016)
    assert fe.a_ecrire(m, [eq("chauffage_principal", "chauffage", "chaudiere_gaz")]) == {
        "chauffage_principal": "gaz", "chauffage_principal_annee": None}


# — Les décisions du 22/10/2026 —

@pytest.mark.parametrize("fiche", ["reseau", "autre"])
def test_un_chauffage_autre_ne_reecrit_pas_un_reseau_de_chaleur(fiche):
    m = maison(chauffage_principal=fiche, chauffage_principal_annee=2000)
    e = eq("chauffage_principal", "chauffage", "autre", annee=2000)
    assert fe.ecarts(m, [e]) == []
    assert fe.a_ecrire(m, [e])["chauffage_principal"] == fiche
    assert "chauffage_principal" in fe.champs_verrouilles([e])  # verrouillé quand même
    # Face à une autre valeur, « autre » est bien écrit.
    assert fe.a_ecrire(maison(chauffage_principal="gaz"), [e])["chauffage_principal"] == "autre"


@pytest.mark.parametrize("origine,categorie", [("ecs", "ecs"), ("ventilation", "ventilation")])
def test_un_type_sans_equivalent_laisse_le_champ_libre(origine, categorie):
    m = maison(**{origine: "solaire" if origine == "ecs" else "naturelle"})
    e = eq(origine, categorie, "autre", annee=2012)
    assert fe.a_ecrire(m, [e]) == {}
    assert fe.champs_verrouilles([e]) == []
    assert fe.champs_a_vider(e) == {}  # ni verrouillé, ni vidé
    assert fe.refus_patch(m, [e], {origine: "gaz"}) == []


def test_une_clim_autre_verrouille_seulement_le_oui():
    e = eq("clim", "clim", "autre")
    assert fe.a_ecrire(maison(clim_type="Pompe de piscine"), [e]) == {"clim": True}
    assert fe.champs_verrouilles([e]) == ["clim"]


def test_le_nombre_de_pieces_climatisees_reste_modifiable():
    m = maison(clim=True, clim_type="Split")
    e = eq("clim", "clim", "split")
    assert "clim_nb_pieces" not in fe.champs_verrouilles([e])
    assert fe.refus_patch(m, [e], {"clim_nb_pieces": 3}) == []


def test_une_origine_dans_la_mauvaise_categorie_ne_fixe_rien():
    assert fe.champs_fiche_depuis(eq("ecs", "chauffage", "chaudiere_gaz")) == {}


# — Le PATCH de la fiche —

def test_le_patch_refuse_seulement_ce_qui_change():
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016, regulation=None)
    e = eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee=2016)
    # `saveBlock` renvoie tout le bloc : les mêmes valeurs passent.
    assert fe.refus_patch(m, [e], {"chauffage_principal": "gaz", "chauffage_principal_annee": 2016,
                                    "regulation": "thermostat"}) == []
    assert fe.refus_patch(m, [e], {"chauffage_principal_annee": 2017}) == ["chauffage_principal_annee"]
    assert fe.refus_patch(m, [e], {"chauffage_principal": None}) == ["chauffage_principal"]


def test_un_equipement_hors_service_ne_verrouille_rien():
    e = eq("chauffage_principal", "chauffage", "chaudiere_gaz", annee=2016, en_service=False)
    assert fe.refus_patch(maison(chauffage_principal="gaz"), [e], {"chauffage_principal": "fioul"}) == []


# — La reprise (migration 0030) —

def test_reprise_l_equipement_gagne_et_laisse_une_trace():
    m = maison(chauffage_principal="PAC_air_air", chauffage_principal_annee=2010,
               ecs="ballon_elec", ecs_annee=2010)
    pac = eq("chauffage_principal", "chauffage", "PAC_air_air", annee=2012)
    ballon = eq("ecs", "ecs", "ballon_elec", annee=2010)
    r = fe.reprise(m, [pac, ballon], AUJOURD_HUI)
    assert r["fiche"] == {"chauffage_principal_annee": 2012}
    assert r["annees"] == {}
    assert len(r["journal"]) == 1
    entree = r["journal"][0]
    assert entree["type"] == "autre" and entree["titre"] == "Fiche mise à jour depuis le carnet"
    assert entree["equipement_id"] == pac.id and "2010" in entree["note"]
    # Relancée sur le résultat : rien de plus.
    appliquer(m, r["fiche"])
    assert fe.reprise(m, [pac, ballon], AUJOURD_HUI) == {"annees": {}, "fiche": {}, "journal": []}


def test_reprise_un_equipement_sans_date_prend_l_annee_de_la_fiche():
    m = maison(chauffage_principal="gaz", chauffage_principal_annee=2016)
    chaudiere = eq("chauffage_principal", "chauffage", "chaudiere_gaz")
    r = fe.reprise(m, [chaudiere], AUJOURD_HUI)
    assert r["annees"] == {chaudiere.id: 2016}
    assert r["fiche"] == {}  # plus d'écart une fois l'année reprise
    assert len(r["journal"]) == 1 and "2016" in r["journal"][0]["note"]
    assert fe.reprise(m, [chaudiere], AUJOURD_HUI)["journal"] == []


def test_reprise_type_different_l_equipement_gagne():
    m = maison(chauffage_principal="fioul", chauffage_principal_annee=1995)
    pac = eq("chauffage_principal", "chauffage", "PAC_air_eau", annee=2021)
    r = fe.reprise(m, [pac], AUJOURD_HUI)
    assert r["fiche"] == {"chauffage_principal": "PAC_air_eau", "chauffage_principal_annee": 2021}
    assert "fioul" in r["journal"][0]["note"] and "1995" in r["journal"][0]["note"]


# — Le pré-audit, inchangé, lit la fiche synchronisée —

def test_le_pre_audit_lit_la_fiche_synchronisee():
    base = dict(code_postal="13001", annee_construction="1975_1988", surface_habitable=100,
                isolation_combles="aucune", isolation_murs="partielle", isolation_plancher="bonne",
                menuiseries="simple", ventilation="VMC_simple", regulation="aucune",
                conso_elec_kwh_an=8000, objectifs=["confort_hiver"])
    fiche_perimee = House(**base, chauffage_principal="fioul", chauffage_principal_annee=1995)
    pac = eq("chauffage_principal", "chauffage", "PAC_air_eau", annee=2021)
    appliquer(fiche_perimee, fe.a_ecrire(fiche_perimee, [pac]))
    juste = House(**base, chauffage_principal="PAC_air_eau", chauffage_principal_annee=2021)
    assert run_audit(fiche_perimee, aujourd_hui=AUJOURD_HUI) == run_audit(juste, aujourd_hui=AUJOURD_HUI)


# — La table inverse sert toujours les suggestions du lot 1 —

def test_les_suggestions_traduisent_toujours_la_fiche():
    m = SimpleNamespace(chauffage_principal="reseau", chauffage_principal_annee=1990,
                        chauffage_appoint=None, ecs=None, clim=None, ventilation=None)
    assert suggestions(m, [])[0]["type"] == "autre"
