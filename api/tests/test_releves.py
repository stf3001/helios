"""Mises en relation, lot 4 : le relevé mensuel — fonctions pures, sans base."""

import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services import releves as rv
from app.services.creneaux import a_paris

P = SimpleNamespace(id=uuid.uuid4(), raison_sociale="Démo Isolation Azur", siret=None)


def lead(moment, prix=60, type_="travaux", partner=P, facturable=True, metier="isolation"):
    return SimpleNamespace(id=uuid.uuid4(), partner_id=partner.id, type=type_, metier=metier, prix_ht=prix,
                           consent_client_at=moment, facturable=facturable)


def test_frontieres_de_mois_a_l_heure_de_paris():
    fin_septembre = a_paris(2026, 9, 30, 23, 30)   # 21 h 30 UTC : septembre à Paris
    debut_octobre = a_paris(2026, 10, 1, 0, 30)    # 22 h 30 UTC le 30 : déjà octobre à Paris
    assert debut_octobre.astimezone(timezone.utc).day == 30
    assert rv.mois_de(fin_septembre) == "2026-09" and rv.mois_de(debut_octobre) == "2026-10"
    leads = [lead(fin_septembre), lead(debut_octobre)]
    assert rv.releve(P, leads, [], "2026-09")["nb_lignes"] == 1
    assert rv.releve(P, leads, [], "2026-10")["lignes"][0]["date"] == "2026-10-01"


def test_fin_octobre_apres_le_passage_a_l_heure_d_hiver():
    # Le 25/10/2026 à 3 h, Paris repasse à UTC+1 : le 31 à 23 h 30 vaut 22 h 30 UTC, encore octobre.
    tard = a_paris(2026, 10, 31, 23, 30)
    assert tard.utcoffset() == timedelta(hours=1)
    assert rv.mois_de(tard) == "2026-10" and rv.mois_de(a_paris(2026, 11, 1, 0, 30)) == "2026-11"
    debut, fin = rv.bornes("2026-10")
    assert debut == datetime(2026, 9, 30, 22, tzinfo=timezone.utc)   # minuit d'été
    assert fin == datetime(2026, 10, 31, 23, tzinfo=timezone.utc)    # minuit d'hiver
    assert rv.bornes("2026-12")[1] == datetime(2026, 12, 31, 23, tzinfo=timezone.utc)


def test_total_et_etats_des_contestations():
    jour = a_paris(2026, 9, 10, 15)
    ok, attente, acceptee, refusee = lead(jour), lead(jour), lead(jour, facturable=False), lead(jour)
    contestations = [SimpleNamespace(lead_id=attente.id, statut="en_attente"),
                     SimpleNamespace(lead_id=acceptee.id, statut="acceptee"),
                     SimpleNamespace(lead_id=refusee.id, statut="refusee")]
    r = rv.releve(P, [ok, attente, acceptee, refusee], contestations, "2026-09")
    etats = {x["lead_id"]: x["etat"] for x in r["lignes"]}
    assert etats[str(attente.id)] == "contestation_en_cours"
    assert etats[str(acceptee.id)] == "contestation_acceptee"
    assert etats[str(refusee.id)] == etats[str(ok.id)] == "facturable"
    assert (r["total_ht"], r["tva"], r["ttc"]) == (120.0, 24.0, 144.0)
    assert [x["lead_id"] for x in r["en_attente"]] == [str(attente.id)]
    assert (r["nb_lignes"], r["nb_facturables"], r["nb_contestees"]) == (4, 2, 3)


def test_ce_qui_n_entre_pas_dans_le_releve():
    jour = a_paris(2026, 9, 10, 15)
    autre = SimpleNamespace(id=uuid.uuid4())
    leads = [lead(jour, type_="energie"), lead(jour, prix=None), lead(jour, partner=autre)]
    assert rv.releve(P, leads, [], "2026-09")["lignes"] == []


def test_aucune_donnee_du_foyer_dans_une_ligne():
    l = lead(a_paris(2026, 9, 10, 15))
    l.contact_nom, l.contact_email, l.contact_telephone = "Camille D.", "c@example.com", "0611223344"
    ligne = rv.releve(P, [l], [], "2026-09", {l.id: "83000"})["lignes"][0]
    assert set(ligne) == {"lead_id", "date", "heure", "metier", "code_postal", "prix_ht", "etat", "contestation_refusee"}
    assert ligne["code_postal"] == "83000"


def test_cloture_au_plus_tot_le_8_du_mois_suivant():
    assert rv.cloture_possible_le("2026-09") == date(2026, 10, 8)
    assert rv.cloture_possible_le("2026-12") == date(2027, 1, 8)
    for faux in ("2026-13", "2026-9", "septembre", "2026-00"):
        with pytest.raises(rv.MoisInvalide):
            rv.lire_mois(faux)
