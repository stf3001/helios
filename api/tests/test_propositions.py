"""Mises en relation, lot 1 : éligibilité, tirage au sort, garde-fous — fonctions pures, sans base."""

import random
import uuid
from collections import Counter
from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.config import settings
from app.services import propositions as pr

SIGNEE = datetime(2026, 10, 1, tzinfo=timezone.utc)


def partenaire(nom, statut="actif", charte=SIGNEE, zones=("83",), metiers=("isolation",), **kw):
    champs = dict(id=uuid.uuid4(), raison_sociale=nom, statut=statut, charte_signee_at=charte, zones=list(zones),
                  metiers=list(metiers), rge=True, note_moyenne=4.5, lien_interet=None)
    champs.update(kw)
    return SimpleNamespace(**champs)


def test_les_reglages_sont_ceux_decides():
    assert (settings.mer_prix_ht_eur, settings.mer_delai_contestation_jours, settings.mer_nb_propositions) == (60, 7, 3)


def test_eligibilite():
    assert pr.eligible(partenaire("A"), "83", "isolation")
    assert not pr.eligible(partenaire("B", statut="suspendu"), "83", "isolation")
    assert not pr.eligible(partenaire("C", statut="en_attente"), "83", "isolation")
    assert not pr.eligible(partenaire("D", charte=None), "83", "isolation")
    assert not pr.eligible(partenaire("E", zones=("06",)), "83", "isolation")
    assert not pr.eligible(partenaire("F", metiers=("pac",)), "83", "isolation")
    assert not pr.eligible(partenaire("G"), None, "isolation")


def test_tirage_jamais_plus_de_trois_et_vraiment_au_hasard():
    eligibles = [partenaire(n) for n in "ABCDE"]
    vus, premiers = Counter(), Counter()
    rng = random.Random(1)
    for _ in range(200):
        tires = pr.tirer(eligibles, settings.mer_nb_propositions, rng)
        assert len(tires) == 3 and len({t.id for t in tires}) == 3
        vus.update(t.raison_sociale for t in tires)
        premiers[tires[0].raison_sociale] += 1
    assert set(vus) == set("ABCDE")      # chaque éligible apparaît
    assert len(premiers) == 5            # et chacun passe en tête : l'ordre est tiré, pas trié
    assert pr.tirer(eligibles[:2], 3, rng) and len(pr.tirer(eligibles[:2], 3, rng)) == 2
    assert pr.tirer([], 3, rng) == []


def test_une_meilleure_note_ne_donne_aucun_avantage():
    meilleur = partenaire("Meilleur", note_moyenne=5.0)
    autres = [partenaire(n, note_moyenne=1.0) for n in "ABCD"]
    rng = random.Random(7)
    tetes = Counter(pr.tirer([meilleur, *autres], 3, rng)[0].raison_sociale for _ in range(500))
    assert tetes["Meilleur"] < 160  # ~1/5 des tirages, pas plus


def test_la_proposition_cache_la_note_avant_trois_avis_et_porte_le_consentement_exact():
    p = partenaire("Isol'Var", lien_interet="Société créée par le fondateur d'Hélios")
    deux = pr.proposition(p, nb_avis=2)
    assert deux["note_moyenne"] is None and deux["lien_interet"] == "Société créée par le fondateur d'Hélios"
    assert pr.proposition(p, nb_avis=3)["note_moyenne"] == 4.5
    assert deux["consentement"] == ("J'accepte que ma demande et les informations de mon projet que j'ai choisies "
                                    "soient transmises à Isol'Var, qui pourra me contacter au sujet de ce projet.")
    assert "siret" not in deux and "email" not in deux


def test_garde_fous_de_creation():
    p = partenaire("A")
    assert pr.refus_creation("locataire", "isolation", p, "83", []) == "Ces travaux se décident avec votre propriétaire."
    assert pr.refus_creation(None, "isolation", p, "83", []).startswith("Indiquez dans votre fiche")
    assert pr.refus_creation("proprietaire", "courtage", p, "83", []) == "Choisissez le métier concerné."
    assert pr.refus_creation("proprietaire", "isolation", partenaire("B", charte=None), "83", []).startswith("Ce partenaire")
    assert pr.refus_creation("en_achat", "isolation", p, "83", []) is None
    doublon = SimpleNamespace(partner_id=p.id, metier="isolation")
    assert "déjà en cours" in pr.refus_creation("proprietaire", "isolation", p, "83", [doublon])
    trois = [SimpleNamespace(partner_id=uuid.uuid4(), metier="isolation") for _ in range(3)]
    assert "déjà 3 demandes" in pr.refus_creation("proprietaire", "isolation", p, "83", trois)
    autre_metier = [SimpleNamespace(partner_id=uuid.uuid4(), metier="pac") for _ in range(3)]
    assert pr.refus_creation("proprietaire", "isolation", p, "83", autre_metier) is None


def test_le_courtage_n_est_pas_un_metier_de_travaux():
    assert "courtage" not in pr.METIERS_TRAVAUX and "solaire" in pr.METIERS_TRAVAUX
