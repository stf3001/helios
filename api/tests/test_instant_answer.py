"""La réponse instantanée — l'action la plus engageante du chat, donc la plus encadrée.

Servir une fiche telle quelle, sans modèle, veut dire qu'il n'y a PERSONNE pour rattraper
une erreur de recherche. Le modèle, lui, voit les huit meilleures fiches et peut corriger ;
une réponse instantanée fausse part au visiteur avec l'assurance d'une fiche validée.

Trois conditions sont testées ici, chacune posée après une mesure sur de vraies questions :

1. Le score (`rag_instant_answer_threshold`, 0,66 — calibré en juillet 2026).
2. Le seuil relevé des relances (`RELANCE_INSTANT_MIN`, 0,70 — calibré le 01/10/2026, après
   qu'une relance sur les panneaux ait failli recevoir la fiche du puits canadien).
3. L'ÉCART avec la fiche suivante (`INSTANT_ECART_MIN` — calibré le 13/10/2026). Mesuré sur
   les questions réellement posées par les visiteurs : « faut-il une batterie avec des
   panneaux » servait, instantanément, la fiche « Mes panneaux fonctionnent-ils pendant une
   coupure de courant ? » — deuxième à 0,008 près. Quand deux fiches sans rapport se
   tiennent d'aussi près, aucune n'est « la » réponse.

Aucune base de données : `instant_answer` travaille sur une liste de résultats, qu'on
fabrique ici.
"""

import uuid

import pytest

from app.core.config import settings
from app.services import rag
from app.services.agents_engine import SOURCES_QR


class FauxDocument:
    def __init__(self, source: str, titre: str = "Une fiche"):
        self.id = uuid.uuid4()
        self.source = source
        self.titre = titre


class FauxChunk:
    def __init__(self, reponse: str = "La réponse de la fiche."):
        self.content = f"Q: Une question ?\nR: {reponse}"


def resultat(score: float, source: str = SOURCES_QR[0], reponse: str = "La réponse de la fiche.") -> dict:
    return {"chunk": FauxChunk(reponse), "document": FauxDocument(source), "score": score}


SEUIL = settings.rag_instant_answer_threshold
ECART = rag.INSTANT_ECART_MIN


def test_une_fiche_nettement_devant_est_servie():
    res = [resultat(0.80, reponse="Il faut isoler d'abord."), resultat(0.60)]
    assert rag.instant_answer(res) == "Il faut isoler d'abord."


def test_sous_le_seuil_de_score_rien_n_est_servi():
    assert rag.instant_answer([resultat(SEUIL - 0.01), resultat(0.40)]) is None


def test_une_source_hors_qr_n_est_jamais_servie_telle_quelle():
    """`cas_terrain` et les sources web ne sont pas des Q/R : leur texte n'est pas une réponse."""
    assert rag.instant_answer([resultat(0.90, source="cas_terrain"), resultat(0.40)]) is None


def test_deux_fiches_au_coude_a_coude_repassent_au_modele():
    """LE cas du 13/10/2026 : rien ne se détache, donc on ne sert rien telle quelle.

    Le modèle, lui, verra les deux fiches et pourra trancher — c'est tout l'intérêt de le
    laisser répondre quand la recherche est indécise.
    """
    res = [resultat(0.671), resultat(0.671 - ECART / 2)]
    assert rag.instant_answer(res) is None


def test_l_ecart_juste_suffisant_est_servi():
    """La borne doit être franchissable : sinon on a supprimé la réponse instantanée."""
    res = [resultat(0.70, reponse="Oui."), resultat(0.70 - ECART * 1.01)]
    assert rag.instant_answer(res) == "Oui."


def test_un_seul_resultat_n_a_pas_de_concurrent():
    """Pas de deuxième fiche = rien ne conteste la première ; l'écart ne s'applique pas."""
    assert rag.instant_answer([resultat(0.80, reponse="Seule.")]) == "Seule."


def test_l_ecart_se_mesure_contre_un_AUTRE_document():
    """Piège à ne pas réintroduire : deux chunks d'une MÊME fiche ne se concurrencent pas.

    Aujourd'hui il y a un chunk par fiche, donc le cas ne se présente pas — mais une source
    web découpe un texte en plusieurs morceaux, et le jour où une fiche en aura deux, mesurer
    l'écart contre son propre doublon le rendrait nul et supprimerait la réponse instantanée
    sans que personne ne comprenne pourquoi.
    """
    doc = FauxDocument(SOURCES_QR[0])
    meme_fiche_2e = {"chunk": FauxChunk("Suite."), "document": doc, "score": 0.80}
    premier = {"chunk": FauxChunk("Oui."), "document": doc, "score": 0.80}
    autre = resultat(0.50)
    assert rag.instant_answer([premier, meme_fiche_2e, autre]) == "Oui."


def test_une_relance_exige_davantage():
    """Le sujet d'une relance est SUPPOSÉ, pas écrit : on demande 0,70 au lieu de 0,66."""
    entre_les_deux = (SEUIL + rag.RELANCE_INSTANT_MIN) / 2
    res = [resultat(entre_les_deux, reponse="Oui."), resultat(0.40)]
    assert rag.instant_answer(res, relance=False) == "Oui."
    assert rag.instant_answer(res, relance=True) is None


def test_une_relance_nette_garde_sa_reponse():
    res = [resultat(0.78, reponse="Oui."), resultat(0.50)]
    assert rag.instant_answer(res, relance=True) == "Oui."


def test_liste_vide():
    assert rag.instant_answer([]) is None


def test_un_chunk_sans_marqueur_de_reponse_n_est_pas_servi():
    """Sans « R: », on ne sait pas où commence la réponse — on ne devine pas."""
    res = [resultat(0.90), resultat(0.40)]
    res[0]["chunk"].content = "Un texte sans la forme Q/R attendue."
    assert rag.instant_answer(res) is None


@pytest.mark.parametrize("ecart", [0.0, 0.001, 0.005, 0.008])
def test_les_ecarts_mesures_sur_les_mauvais_cas_sont_tous_refuses(ecart):
    """Les quatre écarts relevés le 13/10/2026 sur des questions mal servies ou douteuses."""
    res = [resultat(0.68), resultat(0.68 - ecart)]
    assert rag.instant_answer(res) is None, f"écart {ecart} : devait repasser au modèle"
