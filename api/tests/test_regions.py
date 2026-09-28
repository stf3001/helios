"""Le decoupage regional — la table qui relie un code postal a un partenaire.

Une erreur ici ne casse rien visiblement : elle envoie simplement un visiteur du Cantal
chez un partenaire qui ne couvre pas sa zone, ou ne lui propose personne. D'ou ces tests,
qui verifient la table plutot qu'un comportement.
"""

import pytest

from app.services import regions


def test_les_treize_regions_metropolitaines_sont_la():
    assert len(regions.REGIONS) == 13


def test_les_96_departements_metropolitains_sont_couverts_une_seule_fois():
    """96 : les 95 numerotes plus la Corse en deux, moins le 20 qui n'existe plus.

    Un departement present dans deux regions ferait remonter deux partenaires solaires
    pour un meme code postal, sans qu'on sache lequel est le bon.
    """
    tous = regions.TOUS_DEPARTEMENTS
    assert len(tous) == 96
    assert len(set(tous)) == 96


@pytest.mark.parametrize("departement,region", [
    ("13", "pac"), ("83", "pac"), ("06", "pac"),
    ("35", "bre"), ("75", "idf"), ("59", "hdf"),
    ("2A", "cor"), ("2B", "cor"), ("974", None), ("99", None),
])
def test_chaque_departement_tombe_dans_la_bonne_region(departement, region):
    assert regions.region_du_departement(departement) == region


@pytest.mark.parametrize("code_postal,departement", [
    ("13100", "13"), ("75011", "75"), ("29200", "29"),
    ("20000", "2A"), ("20600", "2B"),      # la Corse se coupe en deux
    ("", None), ("AB123", None),
])
def test_le_code_postal_donne_son_departement(code_postal, departement):
    assert regions.departement_du_code_postal(code_postal) == departement


def test_les_metiers_de_l_annuaire_sont_ceux_du_seed():
    """Si un metier disparait de la liste, le seed le placerait dans le vide."""
    from scripts.seed_partenaires import PARTENAIRES
    for zones, metiers, _ in PARTENAIRES.values():
        for metier in metiers:
            assert metier in regions.METIERS, metier


def test_chaque_departement_a_exactement_un_partenaire_solaire():
    """AD Solar en PACA, Ensol ailleurs : aucun trou, aucun doublon.

    C'est la promesse faite au visiteur — « Helios saura qui conseiller ». Un departement
    sans partenaire la casse en silence.
    """
    from scripts.seed_partenaires import PARTENAIRES
    couverture: dict[str, list[str]] = {}
    for nom, (zones, metiers, _) in PARTENAIRES.items():
        if "solaire" not in metiers:
            continue
        for zone in zones:
            couverture.setdefault(zone, []).append(nom)

    for departement in regions.TOUS_DEPARTEMENTS:
        assert couverture.get(departement), f"aucun partenaire solaire en {departement}"
        assert len(couverture[departement]) == 1, (departement, couverture[departement])

    assert couverture["13"] == ["AD Solar"]
    assert couverture["35"] == ["Ensol"]


def test_chaque_region_a_son_partenaire_isolation():
    from scripts.seed_partenaires import ISOLATION_PROVISOIRE
    assert set(ISOLATION_PROVISOIRE) == set(regions.REGIONS)
