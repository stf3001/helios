"""Bloc « À faire ce mois-ci », derniers faits et journal fusionné (carnet, lot 4) — sans base."""

from datetime import date, datetime, timezone
from pathlib import Path

from app.services.a_faire import a_faire, derniers_faits, journal_fusionne
from app.services.entretien import charger_taches, echeances

AUJ = date(2026, 10, 21)


def _e(statut, jours, nature="recommande", libelle=None):
    ech = None if statut == "a_planifier" else date.fromordinal(AUJ.toordinal() + jours)
    return {"statut": statut, "echeance": ech, "nature": nature, "libelle": libelle or f"{statut}{jours}",
            "equipement_id": "eq"}


def _g(statut, fin):
    return {"statut": statut, "fin": fin, "libelle": f"garantie {statut}", "provenance": "travaux"}


def test_composition_et_ordre():
    echs = [_e("en_retard", -20), _e("ce_mois", 10), _e("bientot", 40), _e("bientot", 50),
            _e("bientot", 60), _e("bientot", 70), _e("a_planifier", 0), _e("plus_tard", 200)]
    r = a_faire(echs, [_g("bientot", date(2026, 11, 30)), _g("en_cours", date(2030, 1, 1))], AUJ)
    assert [(l["kind"], l["statut"]) for l in r["lignes"]] == [
        ("tache", "en_retard"), ("tache", "ce_mois"),
        ("tache", "bientot"), ("tache", "bientot"), ("tache", "bientot"),  # 3 « bientôt » au plus
        ("garantie", "bientot"),
    ]
    assert r["rien_d_urgent"] is False and r["masquees"] == 0 and r["prochaine"] is None


def test_plafond_de_six_lignes():
    echs = [_e("en_retard", -i) for i in range(1, 6)] + [_e("ce_mois", 5), _e("bientot", 40)]
    r = a_faire(echs, [_g("bientot", date(2026, 12, 1))], AUJ)
    assert len(r["lignes"]) == 6 and r["masquees"] == 2
    assert all(l["kind"] == "tache" for l in r["lignes"])


def test_table_vide_les_garanties_restent():
    r = a_faire([], [_g("bientot", date(2026, 11, 2)), _g("expiree", date(2025, 1, 1))], AUJ, table_vide=True)
    assert r["table_vide"] is True
    assert [l["kind"] for l in r["lignes"]] == ["garantie"]


def test_rien_d_urgent_donne_la_prochaine_echeance():
    echs = [_e("a_planifier", 0), _e("plus_tard", 300, libelle="loin"), _e("plus_tard", 120, libelle="près")]
    r = a_faire(echs, [_g("en_cours", date(2030, 1, 1))], AUJ)
    assert r["lignes"] == [] and r["rien_d_urgent"] is True
    assert r["prochaine"]["libelle"] == "près"
    assert a_faire([], [], AUJ)["prochaine"] is None


def test_derniers_faits_garde_la_date_la_plus_recente():
    entrees = [
        {"tache_id": "t", "equipement_id": "a", "date": date(2024, 5, 1)},
        {"tache_id": "t", "equipement_id": "a", "date": date(2025, 9, 1)},
        {"tache_id": "t", "equipement_id": None, "date": date(2025, 1, 1)},
        {"tache_id": None, "equipement_id": "a", "date": date(2026, 1, 1)},  # entrée libre : ignorée
    ]
    assert derniers_faits(entrees) == {("t", "a"): date(2025, 9, 1), ("t", None): date(2025, 1, 1)}


def test_c_est_fait_sur_une_tache_en_retard_decale_l_echeance():
    """De bout en bout dans le moteur : la date saisie devient la référence."""
    taches = charger_taches(Path(__file__).parent / "fixtures" / "entretien_exemple.json", strict=True)
    pac = {"id": "pac", "categorie": "chauffage", "type": "PAC_air_eau", "date_pose": date(2020, 3, 15),
           "annee_pose": None, "en_service": True, "puissance": None, "unite": None}
    avant = [e for e in echeances([pac], taches, {}, AUJ) if e["tache_id"] == "exemple-pac-24-mois"][0]
    assert avant["statut"] == "en_retard" and avant["echeance"] == date(2022, 3, 15)
    faits = derniers_faits([{"tache_id": "exemple-pac-24-mois", "equipement_id": "pac", "date": date(2026, 10, 2)}])
    apres = [e for e in echeances([pac], taches, faits, AUJ) if e["tache_id"] == "exemple-pac-24-mois"][0]
    assert (apres["provenance"], apres["echeance"], apres["statut"]) == ("journal", date(2028, 10, 2), "plus_tard")


def test_journal_fusionne_dans_l_ordre():
    entrees = [{"id": "j1", "date": date(2025, 6, 1), "type": "entretien", "titre": "Entretien PAC",
                "equipement_id": "pac", "document_id": "doc"},
               {"id": "j2", "date": date(2026, 2, 3), "type": "reparation", "titre": "Fuite", "equipement_id": None}]
    travaux = [{"id": "t1", "nature": "Combles", "date_reception": date(2025, 11, 20),
                "created_at": datetime(2026, 10, 1, tzinfo=timezone.utc), "facture_document_id": None},
               {"id": "t2", "nature": "Toiture", "date_reception": None,
                "created_at": datetime(2026, 10, 10, tzinfo=timezone.utc), "facture_document_id": None}]
    lignes = journal_fusionne(entrees, travaux)
    assert [l["id"] for l in lignes] == ["t2", "j2", "t1", "j1"]
    assert [l["source"] for l in lignes] == ["travaux", "journal", "travaux", "journal"]
    assert lignes[0]["date_reception_connue"] is False and lignes[3]["justifie"] is True
    filtre = journal_fusionne(entrees, travaux, equipement_id="pac", travaux_de_l_equipement=frozenset({"t1"}))
    assert [l["id"] for l in filtre] == ["t1", "j1"]
