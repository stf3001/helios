"""Le « Dossier de la maison » en PDF (carnet, lot 6) — trois maisons, sans base.

Les trois maisons du brief (code postal seul, moyenne, complète) servent aussi aux rendus
visuels du débrief : `maisons()` rend les arguments de `dossier_pdf` déjà calculés par les
vrais moteurs, comme le fait la route.
"""

import io
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from app.services import pdf_dossier
from app.services.a_faire import derniers_faits, journal_fusionne
from app.services.entretien import CHEMIN_TABLE, charger_taches, echeances
from app.services.garanties import age_ans, fin_garanties_chantier, statut_garantie
from app.services.pieces import resume_pieces

AUJ = date(2026, 10, 21)
TACHES = charger_taches(CHEMIN_TABLE, strict=True)
PDL = "12345678901234"

_CHAMPS_FICHE = (
    "code_postal type_logement statut annee_construction surface_habitable nb_niveaux nb_occupants "
    "residence_principale isolation_combles isolation_combles_annee isolation_murs isolation_murs_annee "
    "isolation_plancher isolation_plancher_annee menuiseries menuiseries_annee ventilation dpe_lettre dpe_annee "
    "chauffage_principal chauffage_principal_annee ecs ecs_annee clim clim_nb_pieces conso_elec_kwh_an "
    "conso_autre_energie_type conso_autre_energie_qte puissance_souscrite option_tarifaire pdl zone_old"
).split()


def _fiche(**kw):
    return SimpleNamespace(**{c: kw.get(c) for c in _CHAMPS_FICHE})


def _eq(i, categorie, type_, **kw):
    e = {"id": f"e{i}", "categorie": categorie, "type": type_, "marque": None, "modele": None, "numero_serie": None,
         "puissance": None, "unite": None, "date_pose": None, "annee_pose": None, "installateur": None,
         "garantie_fabricant_fin": None, "contrat_entretien": None, "contrat_prestataire": None, "travaux_id": None,
         "origine_fiche": None, "en_service": True, "note": None}
    e.update(kw)
    e["age_ans"], e["age_statut"] = age_ans(e, AUJ)
    return e


def _chantier(i, nature, entreprise, reception, facture=None):
    t = {"id": f"t{i}", "nature": nature, "entreprise": entreprise, "date_reception": reception, "montant_ttc": 9999,
         "facture_document_id": facture, "attestation_assurance_document_id": None, "note": None,
         "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc)}
    t["garanties"] = [{**g, "statut": statut_garantie(g["fin"], AUJ)}
                      for g in (fin_garanties_chantier(reception) if reception else [])]
    return t


def _arguments(house, equipements=(), travaux=(), pieces=(), emetteurs=(), entrees=(), documents=()):
    return dict(
        house=house, equipements=list(equipements), travaux=list(travaux), pieces=list(pieces),
        emetteurs=list(emetteurs), resume=resume_pieces(house, pieces, emetteurs) if pieces else None,
        echeances=echeances(equipements, TACHES, derniers_faits(entrees), AUJ, maison=house),
        journal=journal_fusionne(entrees, travaux), documents=list(documents), aujourd_hui=AUJ,
    )


def maisons() -> dict:
    minimale = _arguments(_fiche(code_postal="83000"))

    moyenne_fiche = _fiche(code_postal="83300", type_logement="maison", statut="proprietaire",
                           annee_construction="1975_1988", surface_habitable=95, nb_niveaux=1,
                           residence_principale=True, isolation_combles="partielle", menuiseries="double",
                           ventilation="naturelle", chauffage_principal="gaz", conso_elec_kwh_an=4200,
                           puissance_souscrite="6", option_tarifaire="base", pdl=PDL, zone_old="ne_sais_pas")
    moyenne_eqs = [
        _eq(1, "chauffage", "chaudiere_gaz", marque="Saunier Duval", date_pose=date(2014, 11, 3),
            puissance=24, unite="kW", contrat_entretien=True, contrat_prestataire="Chauffage Martin"),
        _eq(2, "ecs", "ballon_elec", marque="Atlantic", annee_pose=2012),
    ]
    moyenne = _arguments(moyenne_fiche, moyenne_eqs,
                         [_chantier(1, "Remplacement des fenêtres du séjour", "Menuiserie du Golfe", date(2024, 4, 18))],
                         entrees=[{"id": "j1", "date": date(2026, 9, 30), "type": "entretien",
                                   "titre": "Entretien annuel de la chaudière", "equipement_id": "e1",
                                   "piece_id": None, "tache_id": "chaudiere-entretien", "intervenant": "Chauffage Martin",
                                   "cout_eur": 145.0, "document_id": None, "note": None}],
                         documents=[SimpleNamespace(type="facture", uploaded_at=datetime(2026, 9, 30))])

    complete_fiche = _fiche(
        code_postal="83990", type_logement="maison", statut="proprietaire", annee_construction="1989_2000",
        surface_habitable=142, nb_niveaux=2, nb_occupants=4, residence_principale=True,
        isolation_combles="bonne", isolation_combles_annee=2023, isolation_murs="partielle", isolation_murs_annee=2010,
        isolation_plancher="aucune", menuiseries="double_recent", menuiseries_annee=2019, ventilation="VMC_simple",
        dpe_lettre="C", dpe_annee=2023, chauffage_principal="PAC_air_eau", ecs="thermodynamique", clim=True,
        clim_nb_pieces=2, conso_elec_kwh_an=7800, conso_autre_energie_type="bois (stères)", conso_autre_energie_qte=3,
        puissance_souscrite="9", option_tarifaire="HPHC", pdl=PDL, zone_old="oui")
    complete_eqs = [
        _eq(1, "chauffage", "PAC_air_eau", marque="Atlantic", modele="Alféa Extensa", numero_serie="SN-PAC-0001",
            date_pose=date(2016, 10, 12), puissance=8, unite="kW", garantie_fabricant_fin=date(2026, 12, 12),
            contrat_entretien=True, contrat_prestataire="Clim'Azur"),
        _eq(2, "chauffage", "poele_bois", marque="Invicta", annee_pose=2018, numero_serie="SN-POELE-02"),
        _eq(3, "ecs", "thermodynamique", marque="Thermor", modele="Aéromax 5", annee_pose=2019, numero_serie="SN-ECS-3"),
        _eq(4, "clim", "multisplit", marque="Daikin", date_pose=date(2021, 6, 2), puissance=5, unite="kW"),
        _eq(5, "ventilation", "VMC_simple", marque="Aldes", annee_pose=2005),
        _eq(6, "production_electricite", "panneaux_pv", marque="DualSun", date_pose=date(2023, 5, 15), puissance=6,
            unite="kWc", garantie_fabricant_fin=date(2048, 5, 15)),
        _eq(7, "eau", "fosse_septique", annee_pose=1995),
        _eq(8, "ecs", "ballon_elec", marque="Atlantic", annee_pose=2008, en_service=False),
    ]
    complete_travaux = [
        _chantier(1, "Isolation des combles perdus", "Isol'Var", date(2025, 12, 21), facture="d1"),
        _chantier(2, "Pose de panneaux photovoltaïques", "AD Solar", date(2023, 5, 15)),
    ]
    pieces = [{"id": f"p{i}", "nom": n, "type": t, "surface_m2": s, "chauffee": c, "orientation": o, "niveau": v}
              for i, (n, t, s, c, o, v) in enumerate([
                  ("Séjour", "sejour", 38, True, "S", 0), ("Cuisine", "cuisine", 14, True, "E", 0),
                  ("Chambre 1", "chambre", 13, True, "SO", 1), ("Chambre 2", "chambre", 11, True, "N", 1),
                  ("Salle de bain", "salle_de_bain", 7, True, None, 1), ("Garage", "garage", 20, False, None, 0)])]
    emetteurs = [
        {"piece_id": "p0", "type": "plancher_chauffant_eau", "nombre": 1, "puissance_w": None},
        {"piece_id": "p0", "type": "poele_bois", "nombre": 1, "puissance_w": 7000},
        {"piece_id": "p1", "type": "plancher_chauffant_eau", "nombre": 1, "puissance_w": None},
        {"piece_id": "p2", "type": "unite_interieure_clim", "nombre": 1, "puissance_w": 2500},
        {"piece_id": "p3", "type": "unite_interieure_clim", "nombre": 1, "puissance_w": 2500},
        {"piece_id": "p4", "type": "seche_serviettes", "nombre": 1, "puissance_w": 500},
    ]
    entrees = []
    journal_brut = [
        (date(2026, 10, 1), "entretien", "Ramonage du conduit", "e2", "ramonage", "Ramoneur Varois", 85, "d2"),
        (date(2026, 9, 20), "entretien", "Entretien du poêle", "e2", "poele-entretien", "Ramoneur Varois", 120, None),
        (date(2026, 7, 4), "entretien", "Filtres des splits", "e4", "clim-filtres", "moi", None, None),
        (date(2026, 6, 2), "entretien", "Détartrage du ballon", "e3", "ballon-detartrage", "moi", None, None),
        (date(2026, 4, 10), "controle", "Inspection des panneaux depuis le sol", "e6", "pv-inspection-visuelle", "moi", None, None),
        (date(2026, 3, 18), "entretien", "Entretien de la PAC", "e1", "pac-entretien", "Clim'Azur", 160, "d3"),
        (date(2026, 3, 1), "entretien", "Test du détecteur de fumée", None, "detecteur-fumee-test", "moi", None, None),
        (date(2026, 1, 15), "reparation", "Remplacement de la sonde extérieure", "e1", None, "Clim'Azur", 95.5, None),
        (date(2025, 11, 30), "amelioration", "Thermostat connecté", None, None, "moi", 189, None),
        (date(2025, 10, 5), "entretien", "Ramonage du conduit", "e2", "ramonage", "Ramoneur Varois", 80, None),
        (date(2025, 6, 12), "entretien", "Nettoyage des bouches de VMC", "e5", "vmc-bouches", "moi", None, None),
        (date(2025, 2, 2), "remplacement", "Nouveau ballon thermodynamique", "e3", None, "Plomberie Varoise", 2890, "d4"),
        (date(2024, 3, 9), "reparation", "Fuite sur le circuit de chauffage", "e1", None, "Clim'Azur", 240, None),
        (date(2023, 9, 1), "controle", "Contrôle SPANC", "e7", "spanc-controle", "SPANC", None, "d5"),
        (date(2022, 5, 20), "autre", "Élagage des arbres près du toit", None, None, "moi", None, None),
    ]
    for i, (d, typ, titre, eq, tache, qui, cout, doc) in enumerate(journal_brut):
        entrees.append({"id": f"j{i}", "date": d, "type": typ, "titre": titre, "equipement_id": eq, "piece_id": None,
                        "tache_id": tache, "intervenant": qui, "cout_eur": cout, "document_id": doc, "note": None})
    documents = [SimpleNamespace(type=t, uploaded_at=datetime(*d)) for t, d in [
        ("dpe", (2023, 6, 1)), ("facture", (2025, 12, 22)), ("facture", (2026, 3, 18)), ("devis", (2026, 8, 30)),
        ("photo", (2026, 10, 10))]]
    complete = _arguments(complete_fiche, complete_eqs, complete_travaux, pieces, emetteurs, entrees, documents)
    return {"minimale": minimale, "moyenne": moyenne, "complete": complete}


def maison_renovee_2024() -> dict:
    """Lot 11 : une maison rénovée en 2024 — PAC air/eau et isolation des combles — avec les
    rubriques du carnet d'information du logement remplies. Sert aussi au rendu du débrief."""
    fiche = _fiche(code_postal="83136", type_logement="maison", statut="proprietaire", annee_construction="1975_1988",
                   surface_habitable=110, nb_niveaux=1, residence_principale=True, isolation_combles="bonne",
                   isolation_combles_annee=2024, menuiseries="double", ventilation="VMC_simple",
                   chauffage_principal="PAC_air_eau", chauffage_principal_annee=2024, conso_elec_kwh_an=6100,
                   puissance_souscrite="9", option_tarifaire="base", zone_old="non")
    combles = _chantier(1, "Isolation des combles perdus", "Isol'Var", date(2024, 3, 12), facture="d1")
    combles.update(categorie_cil="isolation_toiture",
                   note="Soufflage de ouate de cellulose sur 80 m², rehausse de la trappe et pare-vapeur autour du conduit.",
                   isolants=[{"nature": "Ouate de cellulose", "marque_reference": "Isocel Ouate Soufflée",
                              "resistance_thermique": 7.5, "conductivite": 0.04, "epaisseur_mm": 300, "surface_m2": 80,
                              "interfaces": "Écart au feu autour du conduit, trappe isolée"}])
    pac = _chantier(2, "Remplacement de la chaudière fioul par une PAC", "Clim'Azur", date(2024, 10, 2), facture="d2")
    pac.update(categorie_cil="chauffage_froid_ecs", note="Dépose de la chaudière fioul et de la cuve ; PAC air/eau 11 kW.")
    eqs = [_eq(1, "chauffage", "PAC_air_eau", marque="Atlantic", modele="Alféa Excellia", date_pose=date(2024, 10, 2),
               puissance=11, unite="kW", travaux_id="t2", mode_evacuation="sans_objet", etiquette_energie="A++"),
           _eq(2, "chauffage", "chaudiere_fioul", annee_pose=1999, en_service=False, mode_evacuation="conduit")]
    documents = [SimpleNamespace(type=t, filename=f, uploaded_at=datetime(*d)) for t, f, d in [
        ("facture", "facture-combles.pdf", (2024, 3, 15)), ("facture", "facture-pac.pdf", (2024, 10, 5)),
        ("plan", "plan-rez-de-chaussee.pdf", (2024, 1, 20)), ("plan", "schema-reseau-chauffage.pdf", (2024, 10, 5))]]
    return _arguments(fiche, eqs, [pac, combles], documents=documents)


def test_le_dossier_reprend_les_rubriques_du_cil():
    _, texte = _texte(pdf_dossier.dossier_pdf(**maison_renovee_2024()))
    plat = " ".join(texte.split())
    assert pdf_dossier.MENTION in plat
    for attendu in ("Isolation de la toiture", "Chauffage, froid, eau chaude", "Ouate de cellulose",
                    "Isocel Ouate Soufflée", "7,5", "0,040", "300 mm", "80 m²", "sans objet, classe A++", "conduit",
                    "Plans, coupes et schémas de réseaux", "plan-rez-de-chaussee.pdf", "Autres documents",
                    "Soufflage de ouate de cellulose"):
        assert attendu in plat, attendu
    for interdit in ("conforme", "certifié", "officiel"):
        assert interdit not in plat.lower(), interdit


def _texte(pdf_bytes: bytes) -> tuple[int, str]:
    lecteur = PdfReader(io.BytesIO(pdf_bytes))
    return len(lecteur.pages), "\n".join(p.extract_text() or "" for p in lecteur.pages)


@pytest.mark.parametrize("nom", ["minimale", "moyenne", "complete"])
def test_trois_maisons_sans_erreur_ni_trou(nom):
    pages, texte = _texte(pdf_dossier.dossier_pdf(**maisons()[nom]))
    assert "Dossier de la maison" in texte
    assert "None" not in texte and "{" not in texte and "}" not in texte
    assert PDL not in texte
    assert pdf_dossier.MENTION in " ".join(texte.split())  # mot pour mot (lot 11)
    for interdit in ("conforme", "certifié", "officiel"):
        assert interdit not in texte.lower(), interdit
    if nom == "minimale":
        assert pages <= 2 and texte.count("Non renseigné") >= 6


def test_numeros_de_serie_seulement_sur_demande():
    args = maisons()["complete"]
    _, sans = _texte(pdf_dossier.dossier_pdf(**args))
    _, avec = _texte(pdf_dossier.dossier_pdf(**args, numeros_serie=True))
    assert "SN-PAC-0001" not in sans and "SN-PAC-0001" in avec


def test_une_section_decochee_disparait():
    args = maisons()["complete"]
    _, texte = _texte(pdf_dossier.dossier_pdf(**args, sections=["logement", "travaux"]))
    assert "Le logement" in texte and "Les travaux et les garanties" in texte
    assert "Les équipements" not in texte and "L'énergie déclarée" not in texte and "Alféa" not in texte


def test_contenu_de_la_maison_complete():
    _, texte = _texte(pdf_dossier.dossier_pdf(**maisons()["complete"]))
    plat = texte.replace("\n", " ")
    assert "Anciens équipements" in plat                       # le ballon déposé, à part
    assert "Parfait achèvement" in plat and "21/12/2026" in plat  # garantie calculée par le moteur
    assert "À vérifier sur votre contrat" in plat
    assert "Élagage" not in plat                                # journal de plus de 24 mois, non justifié
    assert "Contrôle SPANC" in plat                             # plus ancien, mais justifié : gardé
    assert "ne sont pas joints" in plat


def test_repli_helvetica_sans_police(tmp_path):
    """Sans police embarquée, le document se génère encore (€ et œ remplacés)."""
    pages, texte = _texte(pdf_dossier.dossier_pdf(**maisons()["complete"], fonts_dir=tmp_path))
    assert pages >= 2 and "Dossier de la maison" in texte and "EUR" in texte
