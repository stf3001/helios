"""La production eolienne — et surtout, d'ou elle vient.

Le risque de ce module n'est pas de mal calculer : c'est de faire passer pour une mesure
locale une estimation relevee a 200 km. Les tests gardent donc autant la tracabilite que
les chiffres.
"""

import pytest

from app.core.config import settings
from app.services import eolien

MARSEILLE = (43.30, 5.40)
BREST = (48.39, -4.49)
CREUSE = (46.17, 1.87)     # aucune station dans sa region


def test_la_station_la_plus_proche_est_bien_la_plus_proche():
    for (lat, lon), attendu in ((MARSEILLE, "Marseille"), (BREST, "Brest")):
        _, ville, distance = eolien.station_la_plus_proche(lat, lon)
        assert ville == attendu
        assert distance < 10


def test_un_lieu_sans_station_dans_sa_region_prend_la_plus_proche_et_le_dit():
    """Trois regions n'ont aucune station : Normandie, Centre-Val de Loire, Bourgogne.

    On ne refuse pas de repondre — on repond, et la distance renvoyee dit a l'ecran de
    quelle distance vient l'estimation.
    """
    _, ville, distance = eolien.station_la_plus_proche(*CREUSE)
    assert ville  # une station a ete trouvee
    assert distance > 100  # et elle est loin : l'ecran doit le montrer


def test_le_profil_annuel_fait_bien_une_annee():
    _, info = eolien.production_horaire(6, *MARSEILLE)
    serie, _ = eolien.production_horaire(6, *MARSEILLE)
    assert len(serie) == eolien.HEURES == 8760
    assert info["station"] == "Marseille"


def test_pas_d_eolienne_pas_de_production():
    serie, info = eolien.production_horaire(0, *BREST)
    assert sum(serie) == 0
    assert info == {}


def test_la_production_croit_avec_la_puissance_posee():
    """Mise a l'echelle lineaire depuis le modele nominal : c'est la methode d'EOLIA."""
    trois = sum(eolien.production_horaire(3, *MARSEILLE)[0])
    six = sum(eolien.production_horaire(6, *MARSEILLE)[0])
    assert six == pytest.approx(2 * trois, rel=1e-6)


def test_brest_produit_bien_plus_que_marseille():
    """La geographie doit se voir : sans cela, l'outil ne sert a rien.

    La Bretagne est ventee, la Provence beaucoup moins. Si ces deux chiffres se
    rapprochent, c'est que le profil de vent n'est plus lu par station.
    """
    brest = sum(eolien.production_horaire(6, *BREST)[0])
    marseille = sum(eolien.production_horaire(6, *MARSEILLE)[0])
    assert brest > 2 * marseille


def test_l_anemometre_recale_la_production():
    """EOLIA prete l'appareil un mois ; le facteur corrige l'estimation de la station."""
    sans = sum(eolien.production_horaire(6, *MARSEILLE)[0])
    plus_vente = sum(eolien.production_horaire(6, *MARSEILLE, facteur=1.2)[0])
    moins_ventee = sum(eolien.production_horaire(6, *MARSEILLE, facteur=0.8)[0])
    assert moins_ventee < sans < plus_vente


def test_la_courbe_de_puissance_respecte_les_seuils_de_la_turbine():
    """Rien sous 2 m/s (vitesse de demarrage), le plateau au-dela de 12."""
    assert eolien.puissance_kw(1.0, 6) == 0
    assert eolien.puissance_kw(5.0, 6) > 0
    assert eolien.puissance_kw(20.0, 6) == pytest.approx(eolien.puissance_kw(14.0, 6))


def test_le_tarif_est_interpole_entre_les_deux_bornes():
    assert eolien.cout_ttc_eur(3) == settings.simu_eolien_cout_min_eur
    assert eolien.cout_ttc_eur(9) == settings.simu_eolien_cout_max_eur
    assert settings.simu_eolien_cout_min_eur < eolien.cout_ttc_eur(6) < settings.simu_eolien_cout_max_eur
    # Hors gamme : on borne plutot que d'extrapoler un prix qui n'existe pas.
    assert eolien.cout_ttc_eur(1) == settings.simu_eolien_cout_min_eur
    assert eolien.cout_ttc_eur(50) == settings.simu_eolien_cout_max_eur
