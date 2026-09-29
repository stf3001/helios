"""Le jardin nourricier — et surtout, l'honnetete de ce qu'il affiche.

Le risque de ce module n'est pas de mal multiplier : c'est de rassurer en mentant. La
demande d'origine etait d'afficher au plus une heure d'entretien par jour « pour ne pas
decourager les debutants ». Ces tests gardent la solution retenue a la place : le temps
est une CONTRAINTE D'ENTREE, jamais un resultat tronque.
"""

import pytest

from app.core.config import settings
from app.services import jardin


def test_le_besoin_est_proportionnel_au_foyer():
    assert jardin.besoin_kg_an(1) == pytest.approx(127.0)
    assert jardin.besoin_kg_an(4) == pytest.approx(508.0)


def test_le_temps_affiche_ne_depasse_jamais_le_budget_demande():
    """L'invariant central : on ne rend jamais un temps plus grand que celui accepte.

    C'est ce qui remplace le plafond a une heure demande au depart. Rien n'est tronque :
    c'est la surface qui s'ajuste, et la couverture le dit.
    """
    for personnes in range(1, settings.jardin_personnes_max + 1):
        for budget in (0.25, 0.5, 1.0, 2.0, 3.0):
            r = jardin.calcul(personnes, heures_jour=budget)
            assert r["budget_heures_jour"] <= budget + 1e-9


def test_une_heure_par_jour_pour_une_famille_de_quatre_ne_promet_pas_l_autonomie():
    """Le chiffre que le debutant verra, et qui doit rester honnete.

    Une heure par jour ne nourrit pas quatre personnes en legumes. Si un jour ce test
    passe au vert avec une couverture de 100 %, c'est qu'une hypothese a ete rendue
    complaisante — pas que le jardinage a change.
    """
    r = jardin.calcul(4, heures_jour=1.0, conduite="debutant")
    assert r["couverture_pct"] < 60
    assert r["surface_totale_m2"] > 0
    # Et ce que couterait vraiment la totalite est calcule, et montre.
    assert r["autonomie"]["heures_jour"] > 1.0
    assert not r["autonomie"]["atteinte"]


def test_le_budget_est_plafonne_au_besoin_reel():
    """Trois heures par jour pour une personne seule ne doit pas proposer un marache.

    Sans ce plafond, le calcul proposerait 400 m2 et de quoi nourrir le quartier.
    """
    r = jardin.calcul(1, heures_jour=3.0, conduite="rodee")
    assert r["couverture_pct"] == 100
    assert r["recolte_kg_an"] <= r["besoin_kg_an"] + 1
    assert r["budget_heures_jour"] < 3.0  # on rend le temps qu'on n'utilise pas
    assert r["autonomie"]["atteinte"]


def test_un_jardin_rode_produit_plus_et_demande_moins_de_temps():
    debutant = jardin.calcul(4, heures_jour=1.0, conduite="debutant")
    rodee = jardin.calcul(4, heures_jour=1.0, conduite="rodee")
    assert rodee["couverture_pct"] > debutant["couverture_pct"]
    assert rodee["autonomie"]["heures_jour"] < debutant["autonomie"]["heures_jour"]


def test_la_saison_est_dite_au_lieu_d_etre_lissee():
    """Une moyenne annuelle seule ferait abandonner en juin. Le mois de pointe sort."""
    r = jardin.calcul(4, heures_jour=1.0)
    assert len(r["mensuel"]) == 12
    assert sum(m["heures"] for m in r["mensuel"]) == pytest.approx(r["heures_an"], rel=0.02)
    assert r["pointe"]["mois"] == "mai"
    # La pointe doit etre nettement au-dessus de la moyenne, sinon elle n'apprend rien.
    assert r["pointe"]["heures_jour"] > r["budget_heures_jour"] * 1.4


def test_la_surface_du_terrain_est_plus_grande_que_la_surface_cultivee():
    """Les allees, le compost et la cabane prennent de la place sans rien produire."""
    r = jardin.calcul(4, heures_jour=1.0)
    assert r["surface_totale_m2"] > r["surface_cultivee_m2"]


def test_les_hypotheses_remontent_toutes_avec_leur_statut():
    r = jardin.calcul(2)
    assert len(r["hypotheses"]) >= 5
    for h in r["hypotheses"]:
        assert h["cle"] and h["valeur"] and h["statut"] in ("relevé", "à confirmer")


def test_les_bornes_sont_refusees_dans_le_domaine():
    """Pas seulement par un curseur a l'ecran : le moteur refuse tout seul."""
    with pytest.raises(ValueError):
        jardin.calcul(0)
    with pytest.raises(ValueError):
        jardin.calcul(settings.jardin_personnes_max + 1)
    with pytest.raises(ValueError):
        jardin.calcul(4, heures_jour=12.0)
    with pytest.raises(ValueError):
        jardin.calcul(4, conduite="permaculture")


@pytest.mark.parametrize(
    "code_postal, attendue",
    [
        ("34000", "sud"),    # Montpellier, Occitanie
        ("13001", "sud"),    # Marseille, PACA
        ("33000", "sud"),    # Bordeaux, Nouvelle-Aquitaine
        ("26000", "sud"),    # Valence : Drome, rattachee au Midi a la main
        ("07000", "sud"),    # Privas : Ardeche, idem
        ("59000", "nord"),   # Lille
        ("75001", "nord"),   # Paris
        ("69001", "nord"),   # Lyon : Auvergne-Rhone-Alpes reste au nord
        ("20000", "sud"),    # Ajaccio, Corse
    ],
)
def test_le_decoupage_en_deux_zones(code_postal, attendue):
    assert jardin.zone(code_postal) == attendue


def test_le_programme_change_avec_la_zone():
    """Le sud sème plus tôt. Si les deux zones donnaient la même chose, découper la
    France en deux n'aurait servi à rien."""
    nord = jardin.programme("59000")
    sud = jardin.programme("34000")
    assert nord["zone"] == "nord" and sud["zone"] == "sud"
    tomate_nord = next(l for l in nord["legumes"] if l["nom"] == "Tomate")
    tomate_sud = next(l for l in sud["legumes"] if l["nom"] == "Tomate")
    assert min(tomate_sud["plantation"]) < min(tomate_nord["plantation"])


def test_sans_code_postal_le_programme_retombe_sur_le_nord():
    """Le nord est la zone la plus tardive : se tromper y fait perdre quinze jours,
    alors que conseiller un semis trop tôt fait perdre les plants."""
    p = jardin.programme(None)
    assert p["zone"] == "nord"
    assert p["zone_deduite"] is False
    assert len(p["legumes"]) > 20


def test_le_calendrier_ne_contient_que_des_mois_valides():
    p = jardin.programme("75001")
    assert len(p["mois"]) == 12
    for legume in p["legumes"]:
        assert legume["nom"] and legume["note"]
        for phase in ("semis_abri", "semis", "plantation", "recolte"):
            assert all(1 <= m <= 12 for m in legume[phase]), (legume["nom"], phase)
        # Un légume sans aucune récolte n'aurait rien à faire dans un programme.
        assert legume["recolte"]


def test_un_code_postal_illisible_ne_fait_pas_tomber_le_calcul():
    """La zone est un complement : sans elle, le calcul doit rester servi."""
    assert jardin.zone("bonjour") is None
    assert jardin.zone(None) is None
    r = jardin.calcul(3, code_postal=None)
    assert r["zone"] is None
    assert r["besoin_kg_an"] > 0
