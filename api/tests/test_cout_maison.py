"""Carnet, lot 10 : ce que coûte la maison — fonctions pures, sans base."""

from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.core.config import settings
from app.services.cout_maison import cout_possession, effet_travaux, poste_entretien
from app.services.simu_engine import prix_kwh

AUJOURD_HUI = date(2026, 10, 22)


def maison(**kw):
    champs = dict(statut="proprietaire", type_logement="maison", conso_elec_kwh_an=None,
                  puissance_souscrite=None, conso_autre_energie_type=None, conso_autre_energie_qte=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def entree(jour, cout, type_="entretien"):
    return SimpleNamespace(date=jour, cout_eur=cout, type=type_)


def _postes(r):
    return {p["code"]: p for p in r["postes"]}


def test_la_maison_vide_n_affiche_aucun_zero():
    r = cout_possession(maison(), None, [], AUJOURD_HUI)
    assert all(p["montant_eur"] is None and p["statut"] is None for p in r["postes"])
    assert r["total_an_eur"] is None and r["total_mois_eur"] is None
    assert r["postes_manquants"] == ["electricite", "autre_energie", "entretien", "assurance", "taxe_fonciere",
                                     "eau", "autre"]


def test_l_electricite_suit_exactement_consommation_fois_prix_de_config():
    p = _postes(cout_possession(maison(conso_elec_kwh_an=9000, puissance_souscrite="9"), None, [], AUJOURD_HUI))["electricite"]
    assert p["prix_eur_kwh"] == prix_kwh(9) == dict(settings.simu_prix_kwh_par_kva)[9]
    assert p["montant_eur"] == round(9000 * prix_kwh(9), 2)
    assert (p["statut"], p["prix_statut"], p["prix_date"]) == ("calcule", "suppose", "2026-08-01")
    assert p["kva_suppose"] is False


def test_sans_puissance_souscrite_le_prix_est_celui_du_preaudit_et_c_est_dit():
    p = _postes(cout_possession(maison(conso_elec_kwh_an=4000), None, [], AUJOURD_HUI))["electricite"]
    assert p["kva"] == settings.audit_puissance_kva_defaut and p["kva_suppose"] is True
    assert p["montant_eur"] == round(4000 * prix_kwh(settings.audit_puissance_kva_defaut), 2)


def test_l_autre_energie_avec_unite_est_chiffree():
    """1 500 L × 10 kWh/L = 15 000 kWh × 0,19 €/kWh = 2 850 € (pré-audit lot 7)."""
    p = _postes(cout_possession(maison(conso_autre_energie_type="fioul", conso_autre_energie_qte=1500,
                                       conso_autre_energie_unite="litres"), None, [], AUJOURD_HUI))["autre_energie"]
    assert (p["montant_eur"], p["statut"], p["conso_kwh_an"]) == (2850, "calcule", 15000)
    assert (p["prix_statut"], p["prix_date"], p["raison"]) == ("suppose", "2026-09-01", None)
    bois = _postes(cout_possession(maison(conso_autre_energie_type="granules", conso_autre_energie_qte=3000,
                                          conso_autre_energie_unite="kg"), None, [], AUJOURD_HUI))["autre_energie"]
    assert bois["montant_eur"] == round(3000 * 4.6 * 0.08, 2) and bois["prix_eur_kwh"] == 0.08


def test_l_autre_energie_sans_unite_n_est_pas_chiffree():
    p = _postes(cout_possession(maison(conso_autre_energie_type="fioul", conso_autre_energie_qte=1500),
                                None, [], AUJOURD_HUI))["autre_energie"]
    assert p["montant_eur"] is None and p["raison"] == "unite_inconnue"


def test_l_entretien_ne_compte_que_les_douze_derniers_mois():
    journal = [
        entree(date(2026, 10, 1), 180),           # compté
        entree(date(2025, 10, 23), 90),           # compté : dans les 12 mois
        entree(date(2025, 10, 22), 1000),         # il y a un an jour pour jour : exclu
        entree(date(2026, 3, 5), 12.5, "reparation"),
        entree(date(2026, 6, 1), None),           # sans coût
        entree(date(2026, 9, 1), 16500, "amelioration"),  # investissement : pas un coût d'usage
        entree(date(2026, 9, 2), 2400, "remplacement"),
    ]
    p = poste_entretien(journal, AUJOURD_HUI)
    assert p["montant_eur"] == 282.5 and p["nb_entrees"] == 3
    assert (p["statut"], p["donnees"]) == ("calcule", "declare")


def test_locataire_sans_taxe_fonciere_maison_sans_copropriete():
    loc = [p["code"] for p in cout_possession(maison(statut="locataire"), None, [], AUJOURD_HUI)["postes"]]
    assert "taxe_fonciere" not in loc and "charges_copro" not in loc
    appart = [p["code"] for p in cout_possession(maison(type_logement="appartement"), None, [], AUJOURD_HUI)["postes"]]
    assert "taxe_fonciere" in appart and "charges_copro" in appart


def test_total_par_an_et_par_mois_sur_les_postes_renseignes():
    charges = SimpleNamespace(assurance_eur_an=420, taxe_fonciere_eur_an=1180, charges_copro_eur_an=None,
                              eau_eur_an=None, autre_eur_an=60, autre_libelle="Ramonage du voisin")
    r = cout_possession(maison(conso_elec_kwh_an=6000, puissance_souscrite="6"), charges,
                        [entree(date(2026, 5, 1), 150)], AUJOURD_HUI)
    elec = round(6000 * prix_kwh(6), 2)
    assert r["total_an_eur"] == round(elec + 150 + 420 + 1180 + 60, 2)
    assert r["total_mois_eur"] == round(r["total_an_eur"] / 12, 2)
    assert r["postes_manquants"] == ["autre_energie", "eau"]
    postes = _postes(r)
    assert postes["assurance"]["statut"] == "declare" and postes["autre"]["libelle"] == "Ramonage du voisin"


AUDIT = {
    "priorites": [
        {"action": "ballon_thermodynamique", "label": "Ballon d'eau chaude thermodynamique", "horizon": "prioritaire",
         "cout_eur": {"bas": 1800, "haut": 2800}, "economie_annuelle_eur": {"bas": 351, "haut": 475, "central": 413},
         "temps_retour_ans": 5.6, "statuts": {"cout_eur": "suppose", "economie_annuelle_eur": "calcule"}},
        {"action": "isolation_combles", "label": "Isolation des combles / toiture", "horizon": "a_l_occasion",
         "cout_eur": {"bas": 2500, "haut": 7000}, "economie_annuelle_eur": {"bas": 80, "haut": 110, "central": 95},
         "temps_retour_ans": 50.1, "statuts": {}},
    ],
    "synthese": {"plan_recommande": {"nb": 1, "investissement_eur": {"bas": 1800, "haut": 2800}}},
}
LE_20_10 = datetime(2026, 10, 20, 8, tzinfo=timezone.utc)


def test_l_effet_des_travaux_recopie_l_audit_tel_quel():
    r = effet_travaux((AUDIT, LE_20_10, "a1"), [])
    assert r["audit"]["date"] == "2026-10-20" and r["audit"]["id"] == "a1"
    for recopie, source in zip(r["audit"]["actions"], AUDIT["priorites"]):
        for cle in ("action", "label", "horizon", "cout_eur", "economie_annuelle_eur", "temps_retour_ans", "statuts"):
            assert recopie[cle] == source[cle]
    assert r["audit"]["plan_recommande"] == AUDIT["synthese"]["plan_recommande"]
    assert r["etudes"] == []


def test_un_audit_v1_ne_donne_pas_d_action_et_pas_d_audit_rien():
    assert effet_travaux(({"actions": [{"cle": "x"}]}, LE_20_10, "a0"), [])["audit"]["actions"] == []
    assert effet_travaux(None, []) == {"audit": None, "etudes": []}


def test_les_etudes_du_simulateur_sont_recopiees():
    resultat = {"indicateurs": {"economie_1re_annee_eur": 640, "temps_retour_ans": 14.2, "puissance_kwc": 5.1},
                "investissement": {"total_eur": 10521}}
    [e] = effet_travaux(None, [(resultat, LE_20_10, "s1", "Toit sud")])["etudes"]
    assert e == {"id": "s1", "date": "2026-10-20", "nom": "Toit sud", "investissement_eur": 10521,
                 "economie_1re_annee_eur": 640, "temps_retour_ans": 14.2, "puissance_kwc": 5.1}
