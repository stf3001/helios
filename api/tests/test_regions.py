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


def _couverture(metier: str) -> dict[str, list[str]]:
    from scripts.seed_partenaires import PARTENAIRES
    couverture: dict[str, list[str]] = {}
    for nom, (zones, metiers, _) in PARTENAIRES.items():
        if metier not in metiers:
            continue
        for zone in zones:
            couverture.setdefault(zone, []).append(nom)
    return couverture


@pytest.mark.parametrize("metier", ["solaire", "pac", "isolation"])
def test_aucun_departement_ne_reste_sans_partenaire(metier):
    """La promesse faite au visiteur : « Helios saura qui conseiller ».

    Un departement sans personne la casse en silence — Helios repondrait « je n'ai
    personne a vous proposer » sans que rien ne signale l'oubli.
    """
    couverture = _couverture(metier)
    for departement in regions.TOUS_DEPARTEMENTS:
        assert couverture.get(departement), f"aucun partenaire {metier} en {departement}"


@pytest.mark.parametrize("metier", ["solaire", "pac", "isolation"])
def test_trois_partenaires_par_departement_pour_pouvoir_comparer(metier):
    """Un seul nom ressemble a une recommandation ; trois laissent le choix.

    C'est ce que la charte demande : Helios oriente, il ne pousse pas. Si ce compte
    change, c'est une decision a prendre, pas un effet de bord d'un seed.
    """
    couverture = _couverture(metier)
    for departement in regions.TOUS_DEPARTEMENTS:
        assert len(couverture[departement]) == 3, (departement, couverture[departement])


def test_les_partenaires_historiques_couvrent_bien_leur_zone():
    """AD Solar sur PACA, Ensol ailleurs : la repartition voulue par Stephane."""
    solaire = _couverture("solaire")
    assert "AD Solar" in solaire["13"]
    assert "AD Solar" not in solaire["35"]
    assert "Ensol" in solaire["35"]
    assert "Ensol" not in solaire["13"]


def test_chaque_region_a_son_partenaire_isolation():
    from scripts.seed_partenaires import ISOLATION_PROVISOIRE, RACINES_REGIONALES
    assert set(ISOLATION_PROVISOIRE) == set(regions.REGIONS)
    assert set(RACINES_REGIONALES) == set(regions.REGIONS)


# --- Normalisation des zones d'un partenaire -------------------------------------
# Le champ etait rempli en texte libre alors que `routers/chat.py` compare la zone au
# departement du visiteur par EGALITE STRICTE : un partenaire ayant declare « 69001 »
# n'etait jamais propose. Ces tests tiennent la regle qui les remet d'accord.

@pytest.mark.parametrize(("saisie", "attendu"), [
    ("13", "13"),            # deja un departement
    ("13100", "13"),         # code postal
    ("69001", "69"),         # celui qui cassait le chat
    ("1", "01"),             # saisie naturelle pour l'Ain
    ("01", "01"),
    ("75020", "75"),         # un arrondissement reste dans son departement
    ("2A", "2A"),            # la Corse par sa lettre
    ("2a", "2A"),            # ... en minuscules
    (" 38 ", "38"),          # espaces parasites
    ("20000", "2A"),         # Ajaccio
    ("20200", "2B"),         # Bastia — le cas que l'ancien prefixe a deux caracteres ratait
])
def test_une_zone_se_ramene_a_son_departement(saisie, attendu):
    assert regions.normaliser_zone(saisie) == attendu


@pytest.mark.parametrize("saisie", ["Lyon", "", "   ", "99", "20", "123", "6900A"])
def test_une_zone_illisible_est_refusee_en_nommant_la_valeur(saisie):
    """Refuser plutot que laisser tomber : une zone qui disparait, c'est un partenaire
    qui ne couvre plus ce qu'il a declare, et il ne l'apprendrait qu'en n'ayant jamais
    de client. « 20 » est refuse a dessein : ce departement n'existe plus."""
    with pytest.raises(regions.ZoneIllisible) as leve:
        regions.normaliser_zone(saisie)
    assert leve.value.valeur == saisie


def test_deux_codes_postaux_du_meme_departement_n_en_font_qu_un():
    """C'est l'exemple que proposait le formulaire public. Un partenaire couvre un
    departement ou ne le couvre pas ; trois arrondissements lyonnais, c'est le Rhone."""
    assert regions.normaliser_zones(["69001", "69002", "38000"]) == ["69", "38"]


def test_toute_zone_normalisee_est_un_departement_connu():
    """Le garde-fou qui relie les deux moities du fichier : ce que la normalisation
    accepte doit exister dans la table des regions, sinon le partenaire est range nulle
    part dans les vignettes du back-office."""
    for dept in regions.TOUS_DEPARTEMENTS:
        assert regions.normaliser_zone(dept) == dept
