"""Le carnet résumé pour le chat (lot 5) — anonyme, court, et jamais une cause de panne."""

import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from app.routers import chat
from app.services import rag
from app.services.a_faire import journal_fusionne
from app.services.carnet_contexte import PLAFOND_CARACTERES, carnet_contexte, taille
from app.services.entretien import charger_taches, echeances
from app.services.garanties import age_ans, garanties_maison
from app.services.pieces import resume_pieces

AUJ = date(2026, 10, 21)
TACHES = charger_taches(Path(__file__).parent / "fixtures" / "entretien_exemple.json", strict=True)
REPERE = "SECRET"  # posé dans chaque champ libre : il ne doit ressortir nulle part


def _eq(i, categorie="chauffage", type_="PAC_air_eau", **kw):
    e = {"id": f"eq{i}", "categorie": categorie, "type": type_, "marque": "Atlantic", "modele": f"{REPERE}-modele",
         "numero_serie": f"{REPERE}-serie", "installateur": f"{REPERE}-installateur", "note": f"{REPERE}-note",
         "contrat_prestataire": f"{REPERE}-prestataire", "contrat_entretien": True, "en_service": True,
         "date_pose": date(2016, 5, 3), "annee_pose": None, "puissance": None, "unite": None,
         "garantie_fabricant_fin": None}
    e.update(kw)
    e["age_ans"], e["age_statut"] = age_ans(e, AUJ)
    return e


def _travaux(i, nature):
    return {"id": f"t{i}", "nature": f"{REPERE} {nature}", "entreprise": f"{REPERE}-entreprise", "montant_ttc": 98765.43,
            "date_reception": date(2025, 12, 20), "created_at": datetime(2025, 12, 1, tzinfo=timezone.utc),
            "facture_document_id": "doc", "attestation_assurance_document_id": None, "note": f"{REPERE}-note-t"}


def _entree(i, jours, **kw):
    e = {"id": f"j{i}", "date": AUJ - timedelta(days=jours), "type": "entretien", "titre": f"{REPERE}-titre",
         "equipement_id": "eq0", "piece_id": None, "tache_id": None, "intervenant": f"{REPERE}-intervenant",
         "cout_eur": 98765.0, "document_id": None, "note": f"{REPERE}-note-j"}
    e.update(kw)
    return e


def _carnet(equipements, travaux, entrees, pieces=None):
    return carnet_contexte(
        equipements, echeances(equipements, TACHES, {}, AUJ, maison={"type_logement": "maison"}),
        garanties_maison(equipements, travaux, AUJ), journal_fusionne(entrees, travaux), pieces, AUJ, travaux=travaux,
    )


def _pieces():
    p = [{"id": "p1", "nom": f"{REPERE}-chambre", "type": "chambre", "surface_m2": 12, "chauffee": True,
          "note": f"{REPERE}-note-p"}, {"id": "p2", "nom": "Séjour", "type": "sejour", "surface_m2": 30, "chauffee": True}]
    e = [{"piece_id": "p2", "type": "radiateur_eau", "nombre": 3, "puissance_w": 1000, "note": f"{REPERE}-note-e"}]
    return resume_pieces({"surface_habitable": 110}, p, e)


def test_aucune_donnee_interdite_ne_sort():
    equipements = [_eq(0, garantie_fabricant_fin=date(2027, 5, 3)),
                   _eq(1, "ecs", "thermodynamique", date_pose=None, annee_pose=2019),
                   _eq(2, "production_electricite", "panneaux_pv", date_pose=date(2023, 4, 1))]
    travaux = [_travaux(0, "Isolation des combles")]
    entrees = [_entree(0, 30, document_id="doc"), _entree(1, 200, type="reparation")]
    carnet = _carnet(equipements, travaux, entrees, _pieces())
    texte = json.dumps(carnet, ensure_ascii=False, default=str)
    assert REPERE not in texte and "98765" not in texte
    for cle in ("numero_serie", "note", "installateur", "intervenant", "entreprise", "titre", "filename",
                "modele", "montant", "cout"):
        assert f'"{cle}' not in texte, cle
    # Ce qu'on attend, en revanche : des codes et des dates, avec leur statut.
    assert {g["objet"] for g in carnet["garanties"]} == {"isolation", "PAC_air_eau"}
    assert set(next(g for g in carnet["garanties"] if g["objet"] == "isolation")["fin"]) == {
        "parfait_achevement", "bon_fonctionnement", "decennale"}
    assert carnet["equipements"][1]["statut"] == "suppose"   # ballon : année seule
    assert carnet["journal"][0] == {"date": "2026-09-21", "type": "entretien", "justifie": True, "pour": "PAC_air_eau"}
    assert carnet["pieces"] == {"nombre": 2, "statut": "declare", "surface_m2": 42, "emetteurs": {"radiateur_eau": 3},
                                "chauffees_sans_emetteur": 1}


def test_ordre_des_equipements_et_limites():
    equipements = [_eq(0, "eau", "adoucisseur"), _eq(1, "production_electricite", "panneaux_pv"),
                   _eq(2, "ecs", "ballon_elec"), _eq(3, "chauffage", "chaudiere_gaz"), _eq(4, en_service=False)]
    carnet = _carnet(equipements, [], [])
    assert [e["categorie"] for e in carnet["equipements"]] == ["chauffage", "ecs", "production_electricite", "eau"]
    vieux = [_entree(i, 800 + i) for i in range(3)]  # plus de 24 mois
    assert "journal" not in _carnet(equipements, [], vieux)


def test_plafond_sur_une_maison_surchargee_et_ordre_de_coupe():
    categories = [("chauffage", "PAC_air_eau"), ("ecs", "ballon_elec"), ("clim", "split"), ("ventilation", "VMC_double"),
                  ("production_electricite", "panneaux_pv"), ("eau", "adoucisseur")]
    equipements = [_eq(i, *categories[i % len(categories)]) for i in range(60)]
    travaux = [_travaux(i, n) for i, n in enumerate(("Isolation", "Toiture", "Menuiseries", "Pose PAC", "VMC"))]
    entrees = [_entree(i, i % 700) for i in range(500)]
    carnet = _carnet(equipements, travaux, entrees, _pieces())
    assert taille(carnet) <= PLAFOND_CARACTERES
    # Coupe dans l'ordre : journal, puis pièces, puis équipements de faible priorité.
    assert "journal" not in carnet and "pieces" not in carnet
    assert 1 <= len(carnet["equipements"]) <= 3
    assert [e["categorie"] for e in carnet["equipements"]][:2] == ["chauffage", "chauffage"]
    assert carnet["echeances"] and carnet["garanties"]          # l'essentiel reste


def test_le_journal_part_avant_les_pieces_et_les_equipements():
    """Une maison juste au-dessus du plafond : seul le journal est rogné."""
    equipements = [_eq(i, c, t) for i, (c, t) in enumerate(
        [("chauffage", "PAC_air_eau"), ("ecs", "ballon_elec"), ("production_electricite", "panneaux_pv")])]
    entrees = [_entree(i, 10 + i, document_id="doc") for i in range(5)]
    sans = carnet_contexte(equipements, [], [], journal_fusionne(entrees, []), _pieces(), AUJ)
    assert taille(sans) <= PLAFOND_CARACTERES and len(sans["journal"]) == 5
    gros = [dict(e, marque="Une marque au nom très très long " * 6) for e in equipements]
    coupe = carnet_contexte(gros, [], [], journal_fusionne(entrees, []), _pieces(), AUJ)
    assert taille(coupe) <= PLAFOND_CARACTERES
    assert len(coupe.get("journal", [])) < 5 and "pieces" in coupe and len(coupe["equipements"]) == 3


def test_maison_sans_carnet_contexte_identique():
    assert _carnet([], [], []) == {}
    maison = SimpleNamespace(__table__=SimpleNamespace(columns=[SimpleNamespace(name="code_postal")]), code_postal="83000")
    rag_compute = rag.compute_score
    try:
        rag.compute_score = lambda h: 0.0
        avant = rag.build_house_context(maison)
        assert rag.build_house_context(maison, carnet={}) == avant
        assert rag.build_house_context(maison, carnet=None) == avant
        assert "carnet" not in avant
        assert rag.build_house_context(maison, carnet={"equipements": [1]})["carnet"] == {"equipements": [1]}
    finally:
        rag.compute_score = rag_compute


class _BaseFactice:
    """Assez de session pour `_carnet_du_foyer` : chaque requête rend une liste vide."""

    async def scalars(self, requete):
        return []


def test_le_chat_tient_si_le_carnet_leve_une_exception(monkeypatch, caplog):
    def panne(*a, **k):
        raise RuntimeError("moteur en panne")

    monkeypatch.setattr(chat, "carnet_contexte", panne)
    maison = SimpleNamespace(id="m1", type_logement="maison")
    with caplog.at_level("ERROR", logger="helios.chat"):
        assert asyncio.run(chat._carnet_du_foyer(_BaseFactice(), maison)) is None
    assert "sans carnet" in caplog.text


def test_le_chat_tient_si_la_base_echoue():
    class BaseEnPanne:
        async def scalars(self, requete):
            raise ConnectionError("base injoignable")

    assert asyncio.run(chat._carnet_du_foyer(BaseEnPanne(), SimpleNamespace(id="m1"))) is None


def test_trois_phrases_dans_le_bloc_connecte():
    contenu = rag.build_user_content("Ma PAC ?", [], house_context={"score": 50, "niveau": "x", "profil": {}})
    assert "La clé \"carnet\" résume les équipements" in contenu
    assert "dis \"d'après votre carnet\" quand tu t'en sers" in contenu
    assert "Ne calcule aucun coût, aucune durée de vie restante ni aucune économie" in contenu
    assert "carnet" not in rag.build_user_content("Ma PAC ?", [])  # visiteur : rien
