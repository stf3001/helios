"""Client Géorisques — SANS RÉSEAU : réponses réelles enregistrées le 22/10/2026 (`fixtures/georisques/`),
servies par un transport httpx simulé (fourni par httpx, aucune dépendance ajoutée)."""
import asyncio
import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.services import georisques as gr

FIX = Path(__file__).parent / "fixtures" / "georisques"
JOUR = date(2026, 10, 22)


def lire(code, nom):
    return json.loads((FIX / code / f"{nom}.json").read_text(encoding="utf-8"))


def transport(code, panne: str | None = None):
    """Rejoue les réponses d'une commune ; `panne` : route qui répond 503."""
    def repondre(request: httpx.Request):
        route = request.url.path.removeprefix("/api/v1/")
        if route == panne:
            return httpx.Response(503, text="")
        if route == "gaspar/catnat":
            page = int(request.url.params.get("page", 1))
            return httpx.Response(200, json=lire(code, "gaspar_catnat")[page - 1])
        return httpx.Response(200, json=lire(code, route.replace("/", "_")))
    return httpx.MockTransport(repondre)


def collecter(code, panne=None):
    async def go():
        async with httpx.AsyncClient(transport=transport(code, panne)) as c:
            return await gr.collecter(code, JOUR, client=c)
    return asyncio.run(go())


def test_commune_du_var_exposee_aux_feux_de_foret():
    r = collecter("83063")
    assert r["commune"] == "LA GARDE-FREINET"
    assert r["risques"] == ["inondation", "argiles", "feux_de_foret", "mouvement_de_terrain", "seisme", "radon",
                            "industriel"]
    assert r["url"].startswith("https://www.georisques.gouv.fr/")
    assert (r["radon_classe"], r["zone_sismique"], r["ppr"]) == (3, 2, True)


def test_commune_argileuse_et_commune_rurale():
    auch = collecter("32013")
    assert "argiles" in auch["risques"] and "feux_de_foret" not in auch["risques"]
    ahun = collecter("23001")
    assert "feux_de_foret" not in ahun["risques"] and "inondation" in ahun["risques"]  # remontée de nappe


def test_catnat_comptees_sur_30_ans_et_toutes_les_pages():
    arretes = [a for page in lire("32013", "gaspar_catnat") for a in page["data"]]
    attendu = sum(1 for a in arretes if gr._date_fr(a["date_debut_evt"]) >= date(1996, 10, 22))
    assert collecter("32013")["catnat_30_ans"] == attendu
    assert gr.compter_catnat([{"date_debut_evt": "21/10/1996"}, {"date_debut_evt": "23/10/1996"},
                              {"date_debut_evt": "illisible"}], JOUR) == 1


def test_une_cle_inconnue_tombe_dans_autre_et_l_ordre_est_fixe():
    rapport = {"commune": {"libelle": "X"}, "url": None,
               "risquesNaturels": {"radon": {"present": True}, "nouveauRisque": {"present": True},
                                   "inondation": {"present": True}, "seisme": {"present": False}},
               "risquesTechnologiques": {"icpe": {"present": False}}}
    assert gr.normaliser_rapport(rapport)["risques"] == ["inondation", "radon", "autre"]


def test_un_changement_d_api_ou_une_panne_leve_une_erreur_propre():
    with pytest.raises(gr.GeorisquesIndisponible):
        gr.normaliser_rapport({"data": []})
    with pytest.raises(gr.GeorisquesIndisponible, match="radon"):
        collecter("83063", panne="radon")
    assert gr.normaliser_radon({"data": [{"classe_potentiel": "?"}]}) is None
    assert gr.normaliser_pprn({}) is None
