"""Carnet, lot 8 : un parcours par statut et par type de logement — fonctions pures, sans base.

La vraie table est utilisée : ce sont ses `responsable` qu'on éprouve, pas une table d'exemple.
"""

import json
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app.services.a_faire import a_faire
from app.services.entretien import (
    CHEMIN_TABLE, MENTION_COPROPRIETE, MENTION_PROPRIETAIRE, charger_taches, echeances, verifications,
)

AUJOURD_HUI = date(2026, 10, 22)  # octobre : aucune tâche écartée par ses `mois_actifs` utiles ici
TACHES = charger_taches(CHEMIN_TABLE, strict=True)
PRECEDENTE = Path(__file__).parent / "fixtures" / "taches_2026-10-20.json"


def eq(categorie, type_, annee=2010):
    return SimpleNamespace(id=uuid.uuid4(), categorie=categorie, type=type_, en_service=True,
                           date_pose=None, annee_pose=annee, puissance=None, unite=None)


def maison(**kw):
    champs = dict(type_logement="maison", statut="proprietaire", zone_old="oui", chauffage_collectif="ne_sais_pas")
    champs.update(kw)
    return SimpleNamespace(**champs)


EQUIPEMENTS = [eq("chauffage", "chaudiere_gaz"), eq("eau", "fosse_septique"), eq("production_electricite", "panneaux_pv"),
               eq("ecs", "ballon_elec")]


def _par_id(lignes):
    return {l["tache_id"]: l for l in lignes}


# — La table : seul `responsable` (et la version) a changé —

def test_seuls_responsable_et_version_ont_change():
    avant = json.loads(PRECEDENTE.read_text(encoding="utf-8"))
    apres = json.loads(CHEMIN_TABLE.read_text(encoding="utf-8"))
    assert apres["version"] == "2026-10-22" and avant["version"] == "2026-10-20"
    assert apres["avertissement"] == avant["avertissement"]
    assert [{k: v for k, v in t.items() if k != "responsable"} for t in apres["taches"]] == avant["taches"]
    proprietaire = {t["id"] for t in apres["taches"] if t["responsable"] == "proprietaire"}
    assert proprietaire == {"spanc-controle", "debroussaillement", "pv-suivi-production", "pv-inspection-visuelle"}


# — Propriétaire occupant : tout lui revient —

def test_le_proprietaire_occupant_voit_tout_pour_lui():
    lignes = echeances(EQUIPEMENTS, TACHES, {}, AUJOURD_HUI, maison=maison())
    assert lignes and all(l["pour_moi"] and l["mention"] is None for l in lignes)
    assert {"spanc-controle", "debroussaillement", "chaudiere-entretien"} <= set(_par_id(lignes))


def test_un_statut_inconnu_compte_comme_proprietaire_occupant():
    lignes = echeances(EQUIPEMENTS, TACHES, {}, AUJOURD_HUI, maison=maison(statut=None))
    assert all(l["pour_moi"] for l in lignes)


# — Locataire —

def test_le_locataire_voit_les_taches_du_proprietaire_en_lecture():
    lignes = _par_id(echeances(EQUIPEMENTS, TACHES, {}, AUJOURD_HUI, maison=maison(statut="locataire")))
    for t in ("spanc-controle", "debroussaillement", "pv-suivi-production"):
        assert lignes[t]["pour_moi"] is False and lignes[t]["mention"] == MENTION_PROPRIETAIRE
    for t in ("chaudiere-entretien", "ballon-groupe-securite", "detecteur-fumee-test"):
        assert lignes[t]["pour_moi"] is True and lignes[t]["mention"] is None


def test_une_tache_du_proprietaire_n_entre_jamais_dans_a_faire():
    lignes = echeances(EQUIPEMENTS, TACHES, {}, AUJOURD_HUI, maison=maison(statut="locataire"))
    assert any(not l["pour_moi"] and l["statut"] == "en_retard" for l in lignes)  # elles sont bien en retard
    bloc = a_faire(lignes, [], AUJOURD_HUI)
    ids = {l["tache_id"] for l in bloc["lignes"]}
    assert ids and not ids & {"spanc-controle", "debroussaillement", "pv-suivi-production", "pv-inspection-visuelle"}


def test_le_locataire_n_a_pas_a_verifier_le_debroussaillement():
    assert [v["tache_id"] for v in verifications(TACHES, maison(zone_old="ne_sais_pas"))] == ["debroussaillement"]
    assert verifications(TACHES, maison(zone_old="ne_sais_pas", statut="locataire")) == []


# — Appartement —

def test_un_appartement_n_a_ni_debroussaillement_ni_spanc():
    lignes = _par_id(echeances(EQUIPEMENTS, TACHES, {}, AUJOURD_HUI,
                               maison=maison(type_logement="appartement")))
    assert "debroussaillement" not in lignes and "spanc-controle" not in lignes
    assert "fosse-niveau-boues" in lignes  # seules les deux tâches nommées disparaissent


def test_chauffage_collectif_chaudiere_assuree_par_la_copropriete():
    m = maison(type_logement="appartement", chauffage_collectif="oui")
    lignes = echeances([eq("chauffage", "chaudiere_gaz"), eq("chauffage", "poele_bois")], TACHES, {}, AUJOURD_HUI, maison=m)
    chaudiere = [l for l in lignes if l["tache_id"] == "chaudiere-entretien"][0]
    assert chaudiere["pour_moi"] is False and chaudiere["mention"] == MENTION_COPROPRIETE
    # Le poêle du foyer reste le sien, ramonage compris.
    poele = [l for l in lignes if l["tache_id"] in ("poele-entretien", "ramonage")]
    assert poele and all(l["pour_moi"] for l in poele)
    assert "chaudiere-entretien" not in {l["tache_id"] for l in a_faire(lignes, [], AUJOURD_HUI)["lignes"]}


def test_chauffage_collectif_sans_effet_sur_une_maison_ni_si_on_ne_sait_pas():
    for m in (maison(chauffage_collectif="oui"), maison(type_logement="appartement", chauffage_collectif="ne_sais_pas")):
        lignes = echeances([eq("chauffage", "chaudiere_gaz")], TACHES, {}, AUJOURD_HUI, maison=m)
        assert all(l["pour_moi"] for l in lignes)
