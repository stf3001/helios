"""Point 81 : le chat reçoit la puissance de chauffage, la plage de PAC, les verdicts des radiateurs
et le relevé de combustible du dernier pré-audit — résumés, sans la traçabilité. Aucun appel au LLM."""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services import rag
from app.services.audit_engine import run_audit
from tests.maisons_combustible import cas
from tests.maisons_puissance import maisons
from tests.test_audit_engine import AUJOURD_HUI

V25 = "tests/fixtures/audit_v25"


def contexte(r: dict) -> dict:
    audit = SimpleNamespace(created_at=datetime(2026, 10, 22), json_result=json.loads(json.dumps(r, default=str)))
    return rag.build_audit_context(audit)


def contexte_maison(nom: str) -> dict:
    h, pieces, emetteurs = maisons()[nom]
    return contexte(run_audit(h, aujourd_hui=AUJOURD_HUI, pieces=pieces, emetteurs=emetteurs))


def test_fioul_six_pieces_reference_plage_et_verdicts():
    p = contexte_maison("fioul_6_pieces")["puissance"]
    assert (p["reference"], p["p_reference_kw"], p["p_conso_kw"], p["p_volume_kw"]) == ("volume", 7.3, 6.6, 7.3)
    assert p["pac_air_eau_kw"] == {"bas": 6.0, "haut": 9.0} and p["texte_plage"].startswith("Une pompe")
    assert p["texte"].startswith("Au jour le plus froid") and p["statut_reference"] == "suppose"
    assert p["radiateurs"] == ["Séjour : ok_55, besoin 2839 W", "Cuisine : insuffisant, besoin 973 W",
                               "Chambre 1 : ok_50, besoin 1136 W", "Chambre 2 : ok_55, besoin 973 W",
                               "Bureau : ok_50, besoin 811 W", "Salle de bains : inconnu, besoin 568 W"]
    brut = json.dumps(p, ensure_ascii=False)
    assert "puissance_50_w" not in brut and "puissance_nominale_w" not in brut and "puissance_55_w" not in brut


def test_la_tracabilite_de_la_puissance_ne_part_pas():
    ctx = contexte_maison("fioul_6_pieces")
    assert not [h for h in ctx["hypotheses"] if h["cle"].startswith(("puissance_", "radiateurs_"))]


def test_convecteurs_phrase_seule_sans_plage():
    p = contexte_maison("convecteurs")["puissance"]
    assert p["reference"] == "consommation" and "pac_air_eau_kw" not in p and "texte_plage" not in p
    assert "radiateurs" not in p


def test_releve_de_fioul_transmis():
    c = contexte(run_audit(cas("fioul_1500_litres"), aujourd_hui=AUJOURD_HUI))["consommation"]
    assert c["releve"] == {"type": "fioul", "unite": "litres", "quantite": 1500}
    assert (c["conso_autre_energie_kwh_an"], c["base_economies"]) == (15000, "declaree")


@pytest.mark.parametrize("nom", sorted(maisons()))
def test_un_audit_v25_n_a_ni_puissance_ni_releve(nom):
    with open(f"{V25}/{nom}.json", encoding="utf-8") as f:
        ctx = contexte(json.load(f))
    assert "puissance" not in ctx and "releve" not in ctx["consommation"]
    # Les clés de consommation d'avant restent toutes là, même vides (contexte inchangé).
    assert "conso_chauffage_declaree_kwh_an" in ctx["consommation"]


def test_un_audit_v1_reste_transmis_tel_quel():
    r = {"version_helios": "v1", "consommation": {"besoin_kwh_m2_an": 180}, "priorites": []}
    assert contexte(r)["resultat"] == r


def test_la_consigne_porte_la_regle_de_puissance():
    assert "Ne jamais proposer une autre puissance" in rag.CONSIGNE_AUDIT_PRIME
    assert "Sans bloc puissance, ne donner aucune puissance de pompe à chaleur" in rag.CONSIGNE_AUDIT_PRIME


def test_taille_du_contexte_maison_au_fioul():
    """Mesuré le 22/10/2026 : 15 099 caractères avant, 16 274 après (+1 175) : consigne du brief
    +631 et son ajustement +246 ; le résumé, net des hypothèses de traçabilité retirées, +298."""
    ctx = contexte_maison("fioul_6_pieces")
    assert len(json.dumps(ctx["puissance"], ensure_ascii=False)) <= 850
    assert len(json.dumps(ctx, ensure_ascii=False)) <= 16300


def test_un_audit_sans_puissance_le_dit_sans_chiffre():
    with open(f"{V25}/fioul_6_pieces.json", encoding="utf-8") as f:
        ctx = contexte(json.load(f))
    assert "refaire le pré-audit" in ctx["puissance_non_calculee"]
    assert "puissance_non_calculee" not in contexte_maison("fioul_6_pieces")


@pytest.mark.parametrize("question, sujet", [
    ("Mes radiateurs suffiront-ils ?", True), ("Quelle puissance de pompe à chaleur ?", True),
    ("Un installateur me propose 14 kW", True), ("Combien de kWh représente mon fioul ?", True),
    ("Comment isoler mes combles ?", False),
])
def test_les_questions_de_puissance_ne_recoivent_pas_de_fiche_toute_faite(question, sujet):
    from app.routers.chat import _SUJET_PUISSANCE
    assert bool(_SUJET_PUISSANCE.search(question)) is sujet
