"""Carnet, lot 11 : « À compléter pour votre carnet d'information du logement » — pur."""

import uuid
from datetime import date
from types import SimpleNamespace

from app.services.cil import a_completer


def chantier(cat, reception=date(2024, 5, 14), note="PAC air/eau à la place de la chaudière fioul"):
    return SimpleNamespace(id=uuid.uuid4(), nature="Travaux", categorie_cil=cat, date_reception=reception, note=note)


def pac(t, **kw):
    champs = dict(id=uuid.uuid4(), travaux_id=t.id, categorie="chauffage", type="PAC_air_eau", marque="Atlantic",
                  modele="Alfea Excellia", numero_serie="SN-1", puissance=11.0, mode_evacuation=None,
                  etiquette_energie=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def test_une_pac_sans_evacuation_ni_etiquette_donne_deux_manques_puis_plus_rien():
    t = chantier("chauffage_froid_ecs")
    e = pac(t)
    [bloc] = a_completer([t], [e], [], [])
    assert bloc["manques"] == [{"objet": "equipement", "id": e.id, "champs": ["mode_evacuation", "etiquette_energie"]}]
    e.mode_evacuation, e.etiquette_energie = "sans_objet", "A++"
    assert a_completer([t], [e], [], [])[0]["manques"] == []


def test_je_ne_sais_pas_laisse_le_manque_ouvert():
    t = chantier("chauffage_froid_ecs")
    e = pac(t, mode_evacuation="inconnu", etiquette_energie="inconnue")
    assert a_completer([t], [e], [], [])[0]["manques"][0]["champs"] == ["mode_evacuation", "etiquette_energie"]


def test_un_chantier_autre_ou_d_avant_2023_ou_sans_reception_n_apparait_pas():
    assert a_completer([chantier("autre")], [], [], []) == []
    assert a_completer([chantier("isolation_toiture", reception=date(2022, 12, 31))], [], [], []) == []
    assert a_completer([chantier("isolation_toiture", reception=None)], [], [], []) == []
    assert a_completer([chantier(None)], [], [], []) == []
    assert len(a_completer([chantier("isolation_toiture", reception=date(2023, 1, 1))], [], [], [])) == 1


def test_isolation_sans_isolant_puis_isolant_incomplet():
    t = chantier("isolation_toiture", note=None)
    manques = a_completer([t], [], [], [])[0]["manques"]
    assert manques == [{"objet": "travaux", "id": t.id, "champs": ["description"]},
                       {"objet": "travaux", "id": t.id, "champs": ["isolant"]}]
    i = SimpleNamespace(id=uuid.uuid4(), travaux_id=t.id, nature="Ouate de cellulose", marque_reference=None,
                        resistance_thermique=7.0, conductivite=None, epaisseur_mm=300, surface_m2=80, interfaces="")
    manques = a_completer([t], [], [i], [])[0]["manques"]
    assert manques[-1] == {"objet": "isolant", "id": i.id, "champs": ["marque_reference", "conductivite", "interfaces"]}


def test_chauffage_sans_equipement_relie():
    t = chantier("chauffage_froid_ecs")
    autre = pac(t, travaux_id=uuid.uuid4())  # posé lors d'un autre chantier
    assert a_completer([t], [autre], [], [])[0]["manques"] == [{"objet": "travaux", "id": t.id, "champs": ["equipement"]}]


def test_un_entretien_note_sans_document_demande_son_attestation():
    t = chantier("chauffage_froid_ecs")
    e = pac(t, mode_evacuation="sans_objet", etiquette_energie="A++")
    sans = SimpleNamespace(id=uuid.uuid4(), equipement_id=e.id, type="entretien", document_id=None)
    avec = SimpleNamespace(id=uuid.uuid4(), equipement_id=e.id, type="entretien", document_id=uuid.uuid4())
    repar = SimpleNamespace(id=uuid.uuid4(), equipement_id=e.id, type="reparation", document_id=None)
    assert a_completer([t], [e], [], [sans, avec, repar])[0]["manques"] == [
        {"objet": "journal", "id": sans.id, "champs": ["attestation"]}]


def test_fenetres_et_portes_ne_demandent_que_la_description():
    assert a_completer([chantier("parois_vitrees_portes")], [], [], [])[0]["manques"] == []
