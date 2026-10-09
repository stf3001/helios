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


# --- Le FICHIER DE DONNEES, et non plus le comportement -------------------------
# Verification du 09/10/2026 (point 5 de TODO.md). Les tests ci-dessus verifient que le
# moteur se comporte bien ; ceux-ci verrouillent la donnee qu'il lit. Un fichier tronque
# ou une unite changee ne cassent rien visiblement : ils deplacent simplement tous les
# chiffres affiches au client, dans le silence.

def test_chaque_station_a_ses_douze_mois_de_vingt_quatre_heures():
    """288 valeurs par station. Un mois manquant decalerait toute l'annee a partir de lui,
    puisque `vitesses_horaires_ms` empile les mois dans l'ordre."""
    profils = eolien._profils()
    assert len(profils) == 12
    for code, profil in profils.items():
        assert sorted(profil) == sorted(str(m) for m in range(1, 13)), code
        for mois, heures in profil.items():
            assert len(heures) == 24, f"{code}/{mois}"


def test_les_vitesses_sont_bien_lues_en_km_h():
    """LE TEST QUI COMPTE LE PLUS ICI. Le fichier donne des km/h, `vitesses_horaires_ms`
    divise par 3,6. Si la source passait un jour en m/s sans qu'on le voie, toutes les
    vitesses seraient multipliees par 3,6 — et la production, qui suit une courbe
    quasi cubique, exploserait sans qu'aucun test de comportement ne bronche.

    On borne donc les moyennes annuelles dans ce qu'un vent de surface francais peut
    valoir : au-dela de 8 m/s de MOYENNE sur l'annee, c'est que l'unite a bouge.
    """
    for code in eolien._profils():
        moyenne = sum(eolien.vitesses_horaires_ms(code)) / eolien.HEURES
        assert 1.0 <= moyenne <= 8.0, f"{code} : {moyenne:.2f} m/s de moyenne annuelle"


def test_le_facteur_de_charge_de_brest_reste_autour_de_26_pourcent():
    """Le chiffre de reference releve avec Stephane. Brest est la station la plus ventee
    du jeu ; si ce facteur bouge, c'est la donnee ou la courbe de puissance qui a change.
    """
    serie, _ = eolien.production_horaire(6.0, 48.39, -4.49)
    facteur_de_charge = sum(serie) / (6.0 * eolien.HEURES)
    assert 0.24 <= facteur_de_charge <= 0.28, f"{facteur_de_charge:.1%}"


def test_aucune_station_ne_depasse_le_plafond_physique_de_la_turbine():
    """La courbe plafonne a 5,05 kW pour une machine dite de 6 kWc : le facteur de charge
    ne peut donc pas depasser 84 %, quel que soit le vent. Un depassement signalerait une
    mise a l'echelle appliquee deux fois."""
    plafond = max(eolien.PUISSANCES_KW) / eolien.NOMINAL_KWC
    for code in eolien._profils():
        vitesses = eolien.vitesses_horaires_ms(code)
        production = sum(eolien.puissance_kw(v, 6.0) for v in vitesses)
        assert production / (6.0 * eolien.HEURES) <= plafond, code
