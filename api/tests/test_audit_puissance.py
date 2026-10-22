"""Pré-audit v2.6 (point 37) : la puissance de chauffage et les radiateurs pièce par pièce.

Les chiffres attendus sont refaits à la main en commentaire. Les quatre maisons de
`maisons_puissance.py` ont leur sortie v2.5 enregistrée : rien d'autre ne doit avoir bougé.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import audit_reference as ref
from app.services.audit_engine import _p_radiateur, deperditions, run_audit
from tests.maisons_puissance import maisons, piece, pieces_fioul
from tests.test_audit_engine import AUJOURD_HUI, maison_type

V25 = Path(__file__).parent / "fixtures" / "audit_v25"


def audit(nom: str) -> dict:
    h, pieces, emetteurs = maisons()[nom]
    return run_audit(h, aujourd_hui=AUJOURD_HUI, pieces=pieces, emetteurs=emetteurs)


def test_les_reglages_du_calcul_a_la_main_tiennent():
    assert settings.audit_t_int == 19
    assert dict(settings.audit_t_base_par_zone)["H3"] == -5 and dict(settings.audit_dju_par_zone)["H3"] == 1500
    assert (settings.audit_hauteur_plafond_m, settings.audit_g_non_isolee, settings.audit_g_min) == (2.5, 1.6, 0.6)
    assert settings.audit_exposant_radiateur == 1.3 and settings.audit_pac_plage_pct == (80, 120)
    assert settings.audit_regimes_radiateurs == ((50, 45), (55, 50))


# --- Les formules, à la main --------------------------------------------------------------

def test_par_la_consommation():
    """Fioul, Marseille (H3), 100 m², 1975-1988 : 180 × 100 × 0,55 / 0,85 = 11 647 kWh de fioul,
    × 0,85 = 9 900 kWh utiles. H = 9 900 000 / (1 500 × 24) = 275 W/K ; × (19 + 5) = 6,6 kW."""
    assert audit("fioul_6_pieces")["puissance"]["p_conso_kw"] == 6.6


def test_au_volume():
    """Indice : 0,28 (combles nus) + 0,23 × 0,6 (murs partiels) + 0,09 × 0,3 (plancher isolé)
    + 0,13 (simple vitrage) + 0,22 × 0,7 (VMC simple) + 0,05 × 0,7 (ponts) = 0,764.
    G = 1,6 × 0,764 = 1,2224 ; 100 × 2,5 × 1,2224 × 24 = 7 334 W → 7,3 kW."""
    b = audit("fioul_6_pieces")["puissance"]
    assert b["p_volume_kw"] == 7.3
    assert b["pac_air_eau_kw"] == {"bas": 6.0, "haut": 9.0}   # 5,87 et 8,80 au demi-kW
    hyp = {h["cle"]: h for h in audit("fioul_6_pieces")["hypotheses"]}
    assert hyp["puissance_indice_isolation"]["valeur"] == 0.764
    assert hyp["puissance_g_w_m3_k"]["statut"] == "calcule" and hyp["puissance_t_base[H3]"]["statut"] == "suppose"


def test_un_radiateur_a_50_et_55_degres():
    """1 000 W donnés pour ΔT = 50 K. 50/45 : ΔT = 47,5 − 19 = 28,5 ; (0,57)^1,3 = 0,4815 → 482 W.
    55/50 : ΔT = 33,5 ; (0,67)^1,3 = 0,5941 → 594 W."""
    assert round(_p_radiateur(1000, 50, 45, 19)) == 482
    assert round(_p_radiateur(1000, 55, 50, 19)) == 594


def test_le_g_ne_descend_pas_sous_son_plancher():
    tres_isolee = maison_type(isolation_combles="bonne", isolation_murs="bonne", menuiseries="triple",
                              ventilation="VMC_double")
    hyp = {h["cle"]: h["valeur"] for h in run_audit(tres_isolee, aujourd_hui=AUJOURD_HUI)["hypotheses"]}
    assert hyp["puissance_g_w_m3_k"] == settings.audit_g_min


# --- La référence et ses textes -------------------------------------------------------------

def test_consommation_declaree_fait_reference():
    b = audit("convecteurs")["puissance"]
    assert b["reference"] == "consommation" and b["p_reference_kw"] == b["p_conso_kw"]
    assert b["statuts"]["p_reference_kw"] == "calcule"
    assert b["texte"] == ("Au jour le plus froid de référence (-5 °C), votre maison demande entre 4,9 et 7,3 kW de "
                          "chauffage. Le calcul tiré de votre consommation réelle (4,9 kW) est le plus juste ; le "
                          "calcul au volume (7,3 kW) sert de repère de prudence.")


def test_consommation_estimee_le_volume_fait_reference():
    b = audit("fioul_6_pieces")["puissance"]
    assert b["reference"] == "volume" and b["p_reference_kw"] == 7.3
    assert b["statuts"] == {"p_conso_kw": "suppose", "p_volume_kw": "suppose", "p_reference_kw": "suppose"}
    assert b["texte"].startswith("Au jour le plus froid de référence (-5 °C), votre maison demande entre 6,6 et 7,3 kW")
    assert b["texte_plage"].startswith("Une pompe à chaleur air/eau d'environ 6 à 9 kW")


def test_ce_que_l_ecran_affiche_selon_la_pac_proposee():
    assert audit("fioul_6_pieces")["puissance"]["affichage"] == "complet"
    convecteurs = audit("convecteurs")["puissance"]   # air/air : la seule phrase de puissance
    assert convecteurs["affichage"] == "puissance" and convecteurs["texte_plage"] is None
    assert audit("reference")["puissance"]["affichage"] is None   # déjà en PAC : rien de proposé


# --- Les radiateurs -------------------------------------------------------------------------

def test_les_verdicts_piece_par_piece():
    """Besoin = 7,3 kW × surface / 90 m² chauffés (le garage n'en est pas). Séjour : 2 839 W ;
    2 × 2 500 W donnent 2 408 W à 50 °C, 2 971 W à 55 °C → ok à 55."""
    r = {x["piece"]: x for x in audit("fioul_6_pieces")["puissance"]["radiateurs"]}
    assert {k: v["verdict"] for k, v in r.items()} == {
        "Séjour": "ok_55", "Cuisine": "insuffisant", "Chambre 1": "ok_50", "Chambre 2": "ok_55",
        "Bureau": "ok_50", "Salle de bains": "inconnu"}
    assert (r["Séjour"]["besoin_w"], r["Séjour"]["puissance_50_w"], r["Séjour"]["puissance_55_w"]) == (2839, 2408, 2971)
    assert r["Salle de bains"]["texte"] == ("Salle de bains : la puissance des radiateurs n'est pas indiquée ; "
                                            "l'installateur doit la relever.")
    assert r["Bureau"]["texte"] == "Bureau : vos radiateurs suffisent avec une eau à 50 °C."


def test_la_somme_des_besoins_egale_la_reference():
    b = audit("fioul_6_pieces")["puissance"]
    assert abs(sum(x["besoin_w"] for x in b["radiateurs"]) - b["p_reference_kw"] * 1000) <= len(b["radiateurs"])


def _bilan(*lignes):
    pieces = [p for p, _ in lignes]
    emetteurs = [e for _, es in lignes for e in es]
    return run_audit(maison_type(), aujourd_hui=AUJOURD_HUI, pieces=pieces, emetteurs=emetteurs)["puissance"]


def test_emetteurs_electriques_sans_surface_et_sans_verdict():
    b = _bilan(piece("Séjour", "sejour", 30, ("radiateur_eau", 1, 3000)),
               piece("Chambre", "chambre", None, ("radiateur_eau", 1, 1500)),
               piece("Bains", "salle_de_bain", 6, ("radiateur_eau", 1, 800), ("seche_serviettes", 1, 500)),
               piece("Bureau", "bureau", 9, ("convecteur", 1, 1000)),
               piece("Salon bois", "autre", 15, ("poele_bois", 1, 6000)),
               piece("Entrée", "entree", 5))
    v = {x["piece"]: x["verdict"] for x in b["radiateurs"]}
    assert v["Chambre"] == "inconnu"            # pas de surface : pas de besoin à comparer
    assert v["Bureau"] == "electrique" and "texte" in b["radiateurs"][3] and b["radiateurs"][3]["texte"] is None
    assert v["Bains"] in ("ok_50", "ok_55", "insuffisant")   # le sèche-serviettes électrique n'y compte pas
    assert "Salon bois" not in v and "Entrée" not in v        # bois, ou rien : aucun verdict
    assert b["note_radiateurs"] is None


def test_toutes_les_pieces_electriques_une_seule_phrase():
    b = _bilan(piece("Séjour", "sejour", 40, ("convecteur", 2, 1500)),
               piece("Chambre", "chambre", 12, ("radiateur_inertie", 1, 1000)))
    assert {x["verdict"] for x in b["radiateurs"]} == {"electrique"}
    assert b["note_radiateurs"] == ref.TEXTES_ACTIONS["pac_air_air"]["note_convecteurs"]


def test_sans_pieces_le_bloc_puissance_seul():
    b = audit("gaz_sans_pieces")["puissance"]
    assert b["affichage"] == "complet" and b["radiateurs"] == [] and b["texte_plage"]


# --- Rien d'autre ne change -----------------------------------------------------------------

def _sans_bloc(r: dict) -> dict:
    """La sortie, sans ce que la v2.6 ajoute : la version, le bloc et ses hypothèses."""
    r = json.loads(json.dumps(r, ensure_ascii=False, default=str, sort_keys=True))
    r.pop("version_helios"); r.pop("puissance", None)
    r["hypotheses"] = [h for h in r["hypotheses"]
                       if not h["cle"].startswith(("puissance_", "radiateurs_"))]
    return r


@pytest.mark.parametrize("nom", sorted(maisons()))
def test_v26_identique_a_v25_hors_puissance(nom):
    v25 = json.loads((V25 / f"{nom}.json").read_text(encoding="utf-8"))
    v25.pop("version_helios")
    assert _sans_bloc(audit(nom)) == v25


def test_les_parts_des_deperditions_sont_inchangees():
    v25 = json.loads((V25 / "fioul_6_pieces.json").read_text(encoding="utf-8"))
    assert deperditions(maison_type()) == v25["deperditions"]


@pytest.mark.parametrize("nom", sorted(maisons()))
def test_aucune_variable_non_remplie(nom):
    b = audit(nom)["puissance"]
    textes = [b["texte"], b["texte_plage"], b["note_radiateurs"]] + [r.get("texte") for r in b["radiateurs"]]
    assert b["texte"] and all("{" not in x for x in textes if x)


def test_un_audit_sans_surface_n_a_pas_de_volume():
    b = run_audit(maison_type(surface_habitable=None), aujourd_hui=AUJOURD_HUI)["puissance"]
    assert b is None or b["p_volume_kw"] is None


def test_pieces_lues_comme_la_base_les_rend():
    """La route passe des objets du modèle : seuls `id`, `nom`, `surface_m2`, `chauffee` et, pour
    les émetteurs, `piece_id`, `type`, `nombre`, `puissance_w` sont lus."""
    pieces, emetteurs = pieces_fioul()
    assert all(isinstance(x, SimpleNamespace) for x in pieces + emetteurs)
