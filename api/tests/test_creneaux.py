"""La grille des creneaux telephoniques — ce qu'on ne doit jamais proposer.

Un creneau propose ENGAGE quelqu'un a appeler. Les tests qui comptent ici sont donc ceux
du refus : pas de week-end, pas de nuit, pas d'appel dans dix minutes, pas dans six mois.
"""

from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.services import creneaux

# Un lundi, en milieu de matinee.
LUNDI = datetime(2026, 9, 28, 10, 0, tzinfo=creneaux.FUSEAU)


def test_aucun_creneau_le_week_end():
    for c in creneaux.proposables(LUNDI):
        assert c.weekday() in settings.rdv_jours_ouvres, c


def test_aucun_creneau_en_dehors_des_heures_d_ouverture():
    ouvertures = settings.rdv_plages_horaires
    for c in creneaux.proposables(LUNDI):
        heure = c.hour + c.minute / 60
        assert any(d <= heure < f for d, f in ouvertures), c


def test_aucun_creneau_avant_le_delai_de_prevenance():
    """Proposer un appel dans dix minutes, c'est promettre ce que personne ne tiendra."""
    plancher = LUNDI + timedelta(hours=settings.rdv_prevenance_h)
    for c in creneaux.proposables(LUNDI):
        assert c >= plancher, c


def test_aucun_creneau_au_dela_de_l_horizon():
    plafond = LUNDI + timedelta(days=settings.rdv_horizon_jours)
    for c in creneaux.proposables(LUNDI):
        assert c <= plafond + timedelta(days=1), c


def test_les_creneaux_sont_espaces_de_la_duree_annoncee():
    """Sinon deux rendez-vous se chevauchent, et le conseiller est en retard des 10 h."""
    par_jour: dict = {}
    for c in creneaux.proposables(LUNDI):
        par_jour.setdefault(c.date(), []).append(c)
    for jour, liste in par_jour.items():
        liste.sort()
        for a, b in zip(liste, liste[1:]):
            ecart = (b - a).total_seconds() / 60
            # Un saut plus grand est normal : c'est la pause de midi.
            assert ecart >= settings.rdv_duree_min, (jour, a, b)


def test_un_creneau_reserve_ne_ressort_pas_des_disponibilites():
    tous = creneaux.proposables(LUNDI)
    pris = {tous[3]}
    libres = creneaux.libres(pris, LUNDI)
    assert tous[3] not in libres
    assert len(libres) == len(tous) - 1


@pytest.mark.parametrize("hors_grille", [
    datetime(2026, 9, 29, 3, 0, tzinfo=creneaux.FUSEAU),     # la nuit
    datetime(2026, 10, 3, 10, 0, tzinfo=creneaux.FUSEAU),    # un samedi
    datetime(2026, 9, 29, 10, 7, tzinfo=creneaux.FUSEAU),    # pas sur le pas de 30 min
    datetime(2027, 3, 1, 10, 0, tzinfo=creneaux.FUSEAU),     # bien au-dela de l'horizon
    datetime(2026, 9, 28, 11, 0, tzinfo=creneaux.FUSEAU),    # avant le delai de prevenance
])
def test_le_serveur_refuse_un_creneau_hors_grille(hors_grille):
    """C'est le serveur qui decide de ses heures, jamais le client.

    Sans ce controle, une requete forgee reserverait un appel a 3 h du matin un dimanche.
    """
    assert not creneaux.est_proposable(hors_grille, LUNDI)


def test_un_creneau_de_la_grille_est_accepte():
    assert creneaux.est_proposable(creneaux.proposables(LUNDI)[0], LUNDI)
