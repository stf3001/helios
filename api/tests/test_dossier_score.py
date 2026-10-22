"""Mises en relation, lot 2 : le dossier transmis et le score — fonctions pures, sans base."""

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.services import dossier_lead as dl
from app.services.score_lead import score

AUJOURD_HUI = date(2026, 10, 22)


def maison(**kw):
    champs = dict(code_postal="83000", type_logement="maison", surface_habitable=110, annee_construction="1975-1988",
                  chauffage_principal="fioul", chauffage_principal_annee=1998, isolation_combles="aucune",
                  isolation_murs="aucune", isolation_plancher="inconnue", menuiseries="simple", horizon="<6mois",
                  budget_envisage="15-30k", completeness_score=85.0, pdl="12345678901234",
                  travaux_deja_faits="Toiture refaite par Martin Couvreur", contraintes="Voisin difficile")
    champs.update(kw)
    return SimpleNamespace(**champs)


PROJET = SimpleNamespace(titre="Isoler les combles", etape="devis", budget_bas_eur=3000, budget_haut_eur=4500,
                         budget_source="audit", budget_statut="calcule", budget_date=date(2026, 9, 1),
                         economie_annuelle_eur=400, economie_source="audit", economie_statut="calcule",
                         economie_date=date(2026, 9, 1), note="Le beau-frère dit que c'est cher",
                         devis_document_ids=["x"])
AUDIT = {"type": "audit", "date": date(2026, 9, 1),
         "contenu": {"priorites": [{"label": "Isoler les combles", "cout_eur": {"bas": 3000, "haut": 4500},
                                    "economie_annuelle_eur": {"central": 400}, "horizon": "maintenant",
                                    "pourquoi": "texte long"}], "pdl": "12345678901234"}}
DOCS = [SimpleNamespace(id=uuid.uuid4(), type="devis", filename="devis.pdf", path="/secret/chemin.pdf")]
TOUT = {"fiche": True, "projet": True, "etude": True}


def construire(house=None, choix=TOUT, **kw):
    args = dict(projet=PROJET, etude=AUDIT, documents=DOCS)
    args.update(kw)
    return dl.construire_dossier(house or maison(), "isolation", "  Devis pour les combles  ", choix,
                                 aujourd_hui=AUJOURD_HUI, **args)


def _texte(obj) -> str:
    return repr(obj)


def test_rien_coche_ne_transmet_que_le_minimum():
    d = construire(choix={}, documents=())
    assert d == {"constitue_le": "2026-10-22",
                 "minimum": {"code_postal": "83000", "type_logement": "maison", "metier": "isolation",
                             "message": "Devis pour les combles"}}


def test_tout_coche_transmet_les_rubriques_choisies_et_rien_d_autre():
    d = construire()
    assert set(d) == {"constitue_le", "minimum", "fiche", "projet", "etude", "documents"}
    assert set(d["fiche"]) == set(dl.CHAMPS_FICHE)
    assert d["projet"]["etape"] == "devis" and d["projet"]["budget_date"] == "2026-09-01"
    assert d["etude"] == {"type": "audit", "date": "2026-09-01", "actions": [
        {"label": "Isoler les combles", "cout_eur": {"bas": 3000, "haut": 4500},
         "economie_annuelle_eur": {"central": 400}, "horizon": "maintenant"}]}
    assert d["documents"] == [{"id": str(DOCS[0].id), "type": "devis", "filename": "devis.pdf"}]


def test_jamais_le_pdl_les_notes_les_intervenants_ni_les_chemins():
    texte = _texte(construire())
    for interdit in ("12345678901234", "Martin Couvreur", "Voisin difficile", "beau-frère", "/secret/", "pdl"):
        assert interdit not in texte


def test_une_case_decochee_vide_la_rubrique_meme_si_l_appelant_la_passe():
    d = construire(choix={"fiche": False, "projet": False, "etude": False})
    assert "fiche" not in d and "projet" not in d and "etude" not in d


def test_etude_du_simulateur_resumee():
    etude = {"type": "simulateur", "date": "2026-10-01T10:00:00",
             "contenu": {"indicateurs": {"puissance_kwc": 6, "economie_1re_annee_eur": 730, "temps_retour_ans": 14.4,
                                         "facture_mois_eur": 50}, "investissement": {"total_eur": 10500}}}
    assert dl.resume_etude(etude) == {"type": "simulateur", "date": "2026-10-01", "puissance_kwc": 6,
                                      "investissement_eur": 10500, "economie_1re_annee_eur": 730,
                                      "temps_retour_ans": 14.4}


def test_creneaux():
    assert dl.valider_creneaux([{"jour": "samedi", "plage": "matin"}, {"jour": "lundi", "plage": "soir"},
                                {"jour": "lundi", "plage": "matin"}, {"jour": "lundi", "plage": "soir"}]) == [
        {"jour": "lundi", "plage": "matin"}, {"jour": "lundi", "plage": "soir"}, {"jour": "samedi", "plage": "matin"}]
    with pytest.raises(dl.DossierInvalide, match="au moins un créneau"):
        dl.valider_creneaux([])
    with pytest.raises(dl.DossierInvalide):
        dl.valider_creneaux([{"jour": "dimanche", "plage": "matin"}])


def _acquis(detail):
    return {d["critere"] for d in detail if d["acquis"]}


def test_score_maison_bien_preparee_tout_partage():
    total, detail = score(construire(), "06 00 00 00 00", AUJOURD_HUI)
    assert total == 100 and len(detail) == 6 and all(d["libelle"] for d in detail)


def test_score_meme_maison_rien_partage_ne_compte_que_le_telephone():
    total, detail = score(construire(choix={}, documents=()), "06 00 00 00 00", AUJOURD_HUI)
    assert (total, _acquis(detail)) == (15, {"telephone"})
    assert score(construire(choix={}, documents=()), "  ", AUJOURD_HUI)[0] == 0


def test_score_maison_en_reflexion_et_etude_ancienne():
    vieux = {**AUDIT, "date": date(2026, 4, 21)}  # plus de 6 mois avant le 22/10
    m = maison(horizon="reflexion", budget_envisage="ne_sait_pas", completeness_score=45.0)
    projet = SimpleNamespace(**{**vars(PROJET), "etape": "idee"})
    total, detail = score(construire(house=m, projet=projet, etude=vieux), None, AUJOURD_HUI)
    assert (total, _acquis(detail)) == (0, set())
    limite = {**AUDIT, "date": date(2026, 4, 22)}
    assert "etude_recente" in _acquis(score(construire(etude=limite), None, AUJOURD_HUI)[1])


def test_score_seuil_de_la_fiche():
    assert "fiche_complete" in _acquis(score(construire(house=maison(completeness_score=60.0)), None, AUJOURD_HUI)[1])
    assert "fiche_complete" not in _acquis(score(construire(house=maison(completeness_score=59.9)), None, AUJOURD_HUI)[1])
