"""Carnet, lot 8 : le parcours par statut, la liste « Avant d'acheter », la note au propriétaire.

Fonctions pures, sans base. Les textes affichés sont recopiés des fiches `kb/` : ces tests
tiennent la source unique, comme `test_audit_textes.py` pour le pré-audit.
"""

import re
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app.services import parcours as pc
from app.services.entretien import CHEMIN_TABLE, charger_taches, echeances
from app.services.note_proprietaire import PHRASES, note

KB = Path(__file__).resolve().parents[2] / "kb"
AUJOURD_HUI = date(2026, 10, 22)


def _section(fiche: str, titre: str) -> dict:
    texte = (KB / f"{fiche}.md").read_text(encoding="utf-8").split(f"## {titre}", 1)[1]
    return dict(re.findall(r"^- \*\*(\w+)\*\* : « (.*) »$", texte, re.M))


def maison(**kw):
    champs = dict(statut="proprietaire", type_logement="maison", zone_old="ne_sais_pas",
                  chauffage_collectif="ne_sais_pas", avant_achat=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


# — Source unique —

def test_la_liste_avant_d_acheter_est_celle_de_la_fiche():
    assert dict(pc.ITEMS_AVANT_ACHAT) == _section("achat_logement", "Pour le carnet")
    assert [i for i, _ in pc.ITEMS_AVANT_ACHAT] == list(_section("achat_logement", "Pour le carnet"))


def test_les_phrases_de_la_note_sont_celles_de_la_fiche():
    assert PHRASES == _section("locataire_entretien", "Pour la note au propriétaire")


def test_la_fiche_d_achat_vers_laquelle_on_renvoie_existe():
    assert f"### Q: {pc.FICHE_ACHAT}\n" in (KB / "achat_logement.md").read_text(encoding="utf-8")


# — Le parcours —

def test_trois_profils_et_un_statut_inconnu():
    assert pc.parcours(maison())["profil"] == "proprietaire"
    assert pc.parcours(maison(statut=None)) == pc.parcours(maison())
    loc = pc.parcours(maison(statut="locataire"))
    assert loc["profil"] == "locataire" and loc["note_proprietaire"]
    assert not loc["voit_travaux"] and not loc["voit_projets_lourds"]
    ach = pc.parcours(maison(statut="en_achat"))
    assert ach["profil"] == "acheteur" and ach["avant_d_acheter"] and ach["voit_travaux"]


def test_le_locataire_ne_voit_pas_les_garanties_de_chantier():
    garanties = [{"provenance": "travaux"}, {"provenance": "equipement"}]
    assert pc.garanties_visibles(garanties, maison(statut="locataire")) == [{"provenance": "equipement"}]
    assert pc.garanties_visibles(garanties, maison()) == garanties


# — Avant d'acheter —

def test_une_maison_a_les_sept_lignes_un_appartement_cinq():
    assert len(pc.avant_achat(maison(statut="en_achat"))) == 7
    ids = [l["id"] for l in pc.avant_achat(maison(statut="en_achat", type_logement="appartement"))]
    assert "debroussaillement" not in ids and "spanc" not in ids and len(ids) == 5
    ids = [l["id"] for l in pc.avant_achat(maison(statut="en_achat", zone_old="non"))]
    assert "debroussaillement" not in ids and "spanc" in ids


def test_les_lignes_portent_ce_qui_a_ete_coche_et_joint():
    m = maison(statut="en_achat", avant_achat={"dpe": {"coche": True, "document_id": "d1"}})
    dpe = pc.avant_achat(m)[0]
    assert dpe == {"id": "dpe", "libelle": pc.ITEMS_AVANT_ACHAT[0][1], "coche": True,
                   "document_id": "d1", "type_document": "dpe"}
    assert pc.avant_achat(m)[1]["coche"] is False and pc.avant_achat(m)[1]["type_document"] == "autre"


def test_l_archive_dit_ce_qui_a_ete_recu():
    m = maison(statut="en_achat", avant_achat={"dpe": {"coche": True, "document_id": "d1"}})
    entree = pc.archive(pc.avant_achat(m), {"d1": "dpe.pdf"}, AUJOURD_HUI)
    assert entree["type"] == "autre" and entree["titre"] == pc.TITRE_ARCHIVE and entree["date"] == AUJOURD_HUI
    lignes = entree["note"].split("\n")
    assert lignes[0] == f"Reçu — {pc.ITEMS_AVANT_ACHAT[0][1]} (document joint : dpe.pdf)"
    assert all(l.startswith("Non reçu — ") for l in lignes[1:]) and len(lignes) == 7


# — La note au propriétaire —

def _eq(categorie, type_, annee):
    return SimpleNamespace(id=uuid.uuid4(), categorie=categorie, type=type_, en_service=True,
                           date_pose=None, annee_pose=annee, puissance=None, unite=None)


def test_la_note_reprend_les_taches_du_proprietaire_et_les_appareils_anciens():
    taches = charger_taches(CHEMIN_TABLE, strict=True)
    equipements = [_eq("eau", "fosse_septique", 2005), _eq("ecs", "ballon_elec", 2020), _eq("chauffage", "convecteurs", 2008)]
    lignes = echeances(equipements, taches, {}, AUJOURD_HUI, maison=maison(statut="locataire", zone_old="oui"))
    texte = note(lignes, equipements, AUJOURD_HUI)
    assert texte.startswith(PHRASES["ouverture"]) and texte.endswith(PHRASES["cloture"])
    assert PHRASES["bail"] in texte
    spanc = next(t["libelle"] for t in taches if t["id"] == "spanc-controle")
    assert f"- {spanc} (Fosse septique) : échéance dépassée" in texte
    # Ce qui revient au locataire n'y est pas : groupe de sécurité du ballon, détecteur de fumée.
    assert "groupe de sécurité" not in texte.lower() and "détecteur" not in texte.lower()
    # Plus de quinze ans : la fosse (2005) et les convecteurs (2008), pas le ballon (2020).
    assert "- Fosse septique\n" in texte + "\n" and "- Convecteurs électriques" in texte
    assert "- Ballon électrique" not in texte
    assert "€" not in texte and not re.search(r"\d", texte)  # ni chiffre ni coût


def test_rien_a_signaler():
    texte = note([], [], AUJOURD_HUI)
    assert PHRASES["rien"] in texte and PHRASES["taches"] not in texte
