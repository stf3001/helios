"""Vigilance météo — SANS RÉSEAU : la carte vient d'une fixture écrite au format documenté."""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.config import settings
from app.services import meteofrance_vigilance as mf
from app.services import vigilance as vg
from app.services import vigilance_lecture as vl
from app.services.agents_engine import _REPO_ROOT, parse_faq_markdown

CARTE = json.loads((Path(__file__).parent / "fixtures" / "meteofrance" / "carte_simulee.json").read_text(encoding="utf-8"))
SOIR = datetime(2026, 10, 22, 20, tzinfo=timezone.utc)
U = timezone.utc


def episodes():
    return mf.normaliser_carte(CARTE)


def test_normalisation_orange_et_rouge_seulement_episodes_fusionnes():
    eps = {(e["departement"], e["phenomene"]): e for e in episodes()}
    assert set(eps) == {("83", "vent"), ("83", "orages"), ("13", "canicule")}  # jaune Nord et littoral ignorés
    vent = eps[("83", "vent")]
    assert (vent["couleur"], vent["debut"], vent["fin"]) == (
        "orange", datetime(2026, 10, 22, 16, tzinfo=U), datetime(2026, 10, 23, 9, tzinfo=U))  # J et J+1 réunis
    assert eps[("13", "canicule")]["couleur"] == "rouge"   # orange puis rouge : la plus forte
    with pytest.raises(mf.VigilanceIndisponible):
        mf.normaliser_carte({"autre": 1})


def test_sans_cle_aucun_appel(monkeypatch):
    monkeypatch.setattr(settings, "meteofrance_api_key", "")
    assert not mf.est_configure()
    with pytest.raises(mf.VigilanceIndisponible, match="dormant"):
        asyncio.run(mf.collecter())

    class Base:  # une base qui échouerait si l'on y touchait
        def __getattr__(self, nom):
            raise AssertionError("la base ne doit pas être lue sans clé")
    assert asyncio.run(vl.collecter_si_besoin(Base())) == "dormant"


def test_le_var_voit_le_vent_le_nord_rien():
    eps = episodes()
    var = vg.vigilances_du_foyer("83", eps, SOIR)
    assert [v["phenomene"] for v in var] == ["vent"]          # les orages sont finis à 11 h
    assert vg.vigilances_du_foyer("59", eps, SOIR) == []      # jaune : rien
    assert vg.vigilances_du_foyer(None, eps, SOIR) == []
    ligne = vg.ligne_a_faire(var[0], SOIR)
    assert ligne["libelle"] == "Vent violent" and ligne["en_cours"] and ligne["autorites"] is None
    assert ligne["gestes"].startswith("Avant le coup de vent") and ligne["carte"].startswith("https://vigilance.meteofrance.fr")


def test_rouge_canicule_demande_de_suivre_les_autorites():
    l = vg.ligne_a_faire(vg.vigilances_du_foyer("13", episodes(), SOIR)[0], SOIR)
    assert l["couleur"] == "rouge" and l["autorites"] == "Suivez les consignes des autorités."
    assert "canicule" in l["question"].lower() and l["gestes"]


def test_fin_d_episode_bandeau_retire_et_noter_un_degat_7_jours():
    eps = episodes()
    assert [a["phenomene"] for a in vg.apres_episode("83", eps, SOIR)] == ["orages"]
    apres = datetime(2026, 10, 23, 10, tzinfo=U)
    assert vg.vigilances_du_foyer("83", eps, apres) == []
    assert {a["phenomene"] for a in vg.apres_episode("83", eps, apres)} == {"vent", "orages"}
    assert [a["phenomene"] for a in vg.apres_episode("83", eps, apres + timedelta(days=7))] == []
    assert vg.apres_episode("13", eps, apres) == []   # la canicule ne laisse pas de « dégât » à noter


def test_neige_verglas_sans_question_et_questions_exactes():
    titres = {e["titre"] for e in parse_faq_markdown(
        (_REPO_ROOT / "helios" / "kb" / "risques_maison.md").read_text(encoding="utf-8"))}
    assert set(vg.QUESTIONS.values()) <= titres
    assert vg.gestes("neige_verglas") is None and vg.gestes("autre") is None


def test_le_chat_recoit_phenomene_couleur_fin():
    r = vg.pour_le_chat(vg.vigilances_du_foyer("83", episodes(), SOIR))
    assert r == [{"phenomene": "vent", "couleur": "orange", "fin": "2026-10-23T09:00", "statut": "observe"}]
    assert vg.pour_le_chat([]) is None
