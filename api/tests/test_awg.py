"""La machine a eau — production, consommation, et le mode « solaire seul ».

Ce qui compte ici n'est pas la precision au litre : c'est que les deux regimes soient
honnetes l'un envers l'autre. Le mode solaire produit MOINS d'eau et ne coute RIEN sur la
facture ; l'ecran doit pouvoir montrer les deux sans que le moteur triche.
"""

import pytest

from app.services import awg

#: Une annee simplifiee : un climat constant, pour raisonner sans le bruit des saisons.
DOUX = ([20.0] * awg.HEURES, [70.0] * awg.HEURES)


def test_les_tables_constructeur_sont_la():
    """Sans elles on ne propose pas la machine : une estimation inventee vaudrait moins que rien."""
    assert awg.tables_disponibles()


@pytest.mark.parametrize("modele", awg.MODELES)
def test_chaque_modele_produit_et_consomme(modele):
    litres, kwh = awg.horaire(modele, *DOUX)
    assert len(litres) == len(kwh) == awg.HEURES
    assert sum(litres) > 0
    assert sum(kwh) > 0


def test_un_plus_gros_modele_produit_plus():
    petit = sum(awg.horaire("20L", *DOUX)[0])
    grand = sum(awg.horaire("100L", *DOUX)[0])
    assert grand > petit


def test_la_chaleur_et_l_humidite_font_la_production():
    """C'est tout le principe : l'AWG condense l'humidite de l'air.

    Un air froid et sec ne donne presque rien. Si ces deux chiffres se rapprochent, c'est
    que la table n'est plus lue.
    """
    chaud_humide = sum(awg.horaire("20L", [30.0] * awg.HEURES, [90.0] * awg.HEURES)[0])
    froid_sec = sum(awg.horaire("20L", [5.0] * awg.HEURES, [30.0] * awg.HEURES)[0])
    assert chaud_humide > 3 * froid_sec


def test_la_consommation_par_litre_reste_dans_l_ordre_de_grandeur_connu():
    """Autour d'un demi-kWh par litre : c'est ce qui rend le pilotage solaire decisif."""
    litres, kwh = awg.horaire("20L", *DOUX)
    par_litre = sum(kwh) / sum(litres)
    assert 0.2 < par_litre < 1.0, par_litre


def test_sans_surplus_la_machine_solaire_ne_produit_rien():
    litres, kwh = awg.horaire("20L", *DOUX)
    l2, k2, reste = awg.sur_surplus(litres, kwh, [0.0] * awg.HEURES)
    assert sum(l2) == 0
    assert sum(k2) == 0
    assert sum(reste) == 0


def test_avec_un_surplus_enorme_la_machine_solaire_tourne_a_plein():
    litres, kwh = awg.horaire("20L", *DOUX)
    l2, k2, reste = awg.sur_surplus(litres, kwh, [999.0] * awg.HEURES)
    assert sum(l2) == pytest.approx(sum(litres))
    assert sum(k2) == pytest.approx(sum(kwh))
    assert sum(reste) > 0  # le surplus non consomme continue son chemin


def test_un_demi_surplus_donne_une_demie_production():
    """La machine module : elle ne s'arrete pas, elle ralentit."""
    litres, kwh = awg.horaire("20L", *DOUX)
    moitie = [k / 2 for k in kwh]
    l2, k2, reste = awg.sur_surplus(litres, kwh, moitie)
    assert sum(l2) == pytest.approx(sum(litres) / 2)
    assert sum(k2) == pytest.approx(sum(kwh) / 2)
    assert sum(reste) == pytest.approx(0.0, abs=1e-6)


def test_le_mode_solaire_produit_toujours_moins_que_la_marche_continue():
    """Le compromis doit rester visible : gratuit, mais moins d'eau."""
    litres, kwh = awg.horaire("20L", *DOUX)
    maigre = [k * 0.3 for k in kwh]
    l2, _, _ = awg.sur_surplus(litres, kwh, maigre)
    assert sum(l2) < sum(litres)
