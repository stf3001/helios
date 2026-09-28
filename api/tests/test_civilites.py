"""Le filet a civilites — et surtout, ce qu'il ne doit JAMAIS attraper.

Le risque de ce module n'est pas de rater un « bonjour » : c'est d'avaler une vraie
question et d'y repondre par une politesse. Un visiteur qui demande « solaire ? » aurait
droit a « Je suis la 🙂 » au lieu d'une reponse — et il ne reviendrait pas.

La moitie basse de ce fichier vaut donc plus que la moitie haute.
"""

import pytest

from app.services import civilites


# --- Ce qui doit etre attrape ---------------------------------------------------

@pytest.mark.parametrize("message", [
    "bonjour", "Bonjour !", "BONJOUR", "bonjour !!!", "Salut", "coucou", "bjr",
    "allo", "allo??", "Alloooo", "allo ?", "?", "???",
    "merci", "Merci beaucoup !", "ok", "Parfait",
    "au revoir", "Bonne journee", "a bientot",
    "ca va ?", "Comment allez-vous ?",
    "qui es-tu ?", "C'est quoi Helios ?", "tu sers a quoi ?",
    "test", "ca marche ?",
])
def test_une_politesse_recoit_une_reponse_ecrite(message):
    reponse = civilites.repondre(message)
    assert reponse is not None, message


def test_les_reponses_sont_courtes_et_vouvoient():
    """Le defaut d'origine : un pave de six lignes qui tutoyait.

    Pas de « tu », pas de « ton/ta/tes », et une longueur qui tient sur deux lignes.
    """
    for formulations, reponse in civilites._CIVILITES:
        assert len(reponse) <= 160, formulations[0]
        mots = civilites.normaliser(reponse).split()
        for interdit in ("tu", "toi", "ton", "ta", "tes", "t es"):
            assert interdit not in mots, f"{formulations[0]} : « {interdit} »"


# --- Ce qui ne doit SURTOUT PAS etre attrape -------------------------------------

@pytest.mark.parametrize("message", [
    "solaire ?",
    "ai-je interet a passer au solaire ?",
    "bonjour, ai-je interet a passer au solaire ?",
    "merci de me dire si ma chaudiere est eligible",
    "quelles aides pour changer ma chaudiere ?",
    "par quoi commencer pour isoler ma maison ?",
    "ca marche vraiment le solaire en hiver ?",
    "ok pour le solaire, et la pompe a chaleur ?",
    "test d'etancheite a l'air, c'est quoi ?",
    "qui es-tu capable de me conseiller sur une PAC ?",
    "bonne journee pour poser des panneaux ?",
])
def test_une_vraie_question_passe_par_la_base_de_connaissances(message):
    assert civilites.repondre(message) is None, message


def test_un_message_vide_ne_declenche_rien():
    """Une chaine vide, ou qui ne contient que des emoji, suit le chemin normal."""
    assert civilites.repondre("") is None
    assert civilites.repondre("   ") is None


def test_la_normalisation_efface_accents_ponctuation_et_emoji():
    assert civilites.normaliser("Bonjour !! 👋") == "bonjour"
    assert civilites.normaliser("Ça va ?") == "ca va ?"
    assert civilites.normaliser("  MERCI   beaucoup  ") == "merci beaucoup"
