"""Le routeur local / API du chat : qui part vers Claude, et quand on l'en empêche.

`choose_route` est pur. Les deux plafonds lisent la base : ici une fausse session renvoie
les totaux qu'aurait calculés Postgres, ce qui vérifie les SEUILS (et l'ordre des
questions posées), pas la requête SQL elle-même.
"""

import asyncio
import uuid

import pytest

from app.core.config import settings
from app.services import router_llm
from app.services.router_llm import choose_route

COURT = "Bonjour"


# --- choose_route -----------------------------------------------------------------------

def test_le_mode_public_reste_toujours_local():
    """Même avec tous les signaux réunis : un visiteur anonyme ne coûte jamais d'API."""
    assert choose_route(mode="public", niveau="preaudit_chiffre",
                        message="combien " + "x" * 500, has_recent_audit=True) == "local"


@pytest.mark.parametrize("niveau", [None, "conseils_generaux", "niveau_inconnu"])
def test_une_fiche_trop_incomplete_reste_locale(niveau):
    assert choose_route(mode="connecte", niveau=niveau, message="combien ça coûte ?",
                        has_recent_audit=True) == "local"


@pytest.mark.parametrize("niveau", ["prediagnostic_qualitatif", "preaudit_chiffre"])
def test_une_question_simple_reste_locale_meme_fiche_complete(niveau):
    assert choose_route(mode="connecte", niveau=niveau, message=COURT) == "local"


@pytest.mark.parametrize("message", [
    "Combien me coûterait une PAC ?",
    "Est-ce RENTABLE chez moi ?",       # « rentab », casse ignorée
    "Explique-moi mon audit",
    "Quel prix pour l'isolation ?",
])
def test_un_mot_cle_bascule_vers_l_api(message):
    assert choose_route(mode="connecte", niveau="prediagnostic_qualitatif",
                        message=message) == "api"


def test_la_longueur_bascule_au_dela_du_seuil_pas_avant():
    seuil = settings.rag_api_long_message_chars
    assert choose_route(mode="connecte", niveau="preaudit_chiffre",
                        message="a" * seuil) == "local"
    assert choose_route(mode="connecte", niveau="preaudit_chiffre",
                        message="a" * (seuil + 1)) == "api"


def test_un_pre_audit_recent_suffit_a_basculer():
    assert choose_route(mode="connecte", niveau="preaudit_chiffre", message=COURT,
                        has_recent_audit=True) == "api"


# --- plafonds ---------------------------------------------------------------------------

class _FausseSession:
    """Rend, dans l'ordre, les valeurs que `db.scalar` aurait obtenues de Postgres."""

    def __init__(self, *valeurs):
        self.valeurs = list(valeurs)
        self.appels = 0

    async def scalar(self, _requete):
        self.appels += 1
        return self.valeurs.pop(0)


UTILISATEUR = uuid.uuid4()


def quota(valeur) -> bool:
    return asyncio.run(router_llm.daily_quota_exceeded(_FausseSession(valeur), UTILISATEUR))


def plafonds(db: _FausseSession) -> bool:
    return asyncio.run(router_llm.cost_caps_exceeded(db, UTILISATEUR))


def test_quota_quotidien_atteint_a_la_n_ieme_requete():
    n = settings.llm_api_daily_requests_per_user
    assert quota(n - 1) is False
    assert quota(n) is True
    assert quota(n + 5) is True


def test_sous_les_deux_plafonds_rien_ne_bloque():
    db = _FausseSession(settings.llm_api_budget_daily_eur - 0.01,
                        settings.llm_api_budget_monthly_eur - 0.01)
    assert plafonds(db) is False
    assert db.appels == 2


def test_le_plafond_du_jour_bloque_sans_regarder_le_mois():
    db = _FausseSession(settings.llm_api_budget_daily_eur, 0.0)
    assert plafonds(db) is True
    assert db.appels == 1


def test_le_plafond_du_mois_bloque_meme_si_le_jour_est_libre():
    """Le mois est GLOBAL (tous clients) : un client sobre est bloqué quand le budget
    partagé est épuisé."""
    db = _FausseSession(0.0, settings.llm_api_budget_monthly_eur)
    assert plafonds(db) is True
    assert db.appels == 2


def test_estimation_du_cout():
    assert router_llm.estimate_cost_eur(None) is None
    assert router_llm.estimate_cost_eur(0) == 0.0
    assert router_llm.estimate_cost_eur(1000) == pytest.approx(settings.llm_price_per_1k_tokens_eur)


def test_une_question_sur_le_carnet_va_a_l_api_quel_que_soit_le_niveau():
    assert choose_route(mode="connecte", niveau="conseils_generaux", message="Quel âge a mon chauffe-eau ?",
                        question_carnet=True) == "api"
    # Le visiteur anonyme n'a pas de carnet : toujours local.
    assert choose_route(mode="public", niveau=None, message="Quel âge a mon chauffe-eau ?",
                        question_carnet=True) == "local"
