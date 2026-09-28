"""Les offres de stockage virtuel — ce que la grille MyLight ne doit pas cesser de dire.

Ces tests ne gardent pas des valeurs pour le plaisir de les garder : ils gardent la
COHERENCE d'une grille recopiee a la main depuis une page produit. Une grille saisie en
plusieurs morceaux se corrige un jour a moitie, et personne ne le voit — sauf ici.

Contexte : jusqu'au 28/09/2026, la restitution du stockage illimite etait chiffree a
0,083 EUR/kWh d'apres deux articles de presse concordants. La grille officielle donne
0,10862. Les deux sources etaient d'accord entre elles, et fausses toutes les deux.
"""

import pytest

from app.core.config import settings
from app.services import batterie_virtuelle


def test_le_cout_de_restitution_est_la_somme_de_ses_trois_lignes():
    """Acheminement + accise + CEE. La grille affiche le total, on verifie qu'il colle.

    C'est le test qui attrape une correction partielle : si l'accise change et que le
    total reste, l'un des deux est faux.
    """
    somme = (settings.mylight_restitution_acheminement_eur_kwh
             + settings.mylight_restitution_accise_eur_kwh
             + settings.mylight_restitution_cee_eur_kwh)
    assert somme == pytest.approx(settings.mylight_restitution_eur_kwh, abs=1e-9)


def test_la_grille_sur_mesure_est_croissante_et_complete():
    """Dix paliers, volumes et prix strictement croissants.

    Un palier plus cher pour moins de volume serait une faute de frappe ; le moteur
    choisit « le plus petit palier qui couvre le besoin » et s'y fierait sans broncher.
    """
    paliers = sorted(settings.simu_msb_paliers)
    assert len(paliers) == 10
    volumes = [kwh for kwh, _ in paliers]
    prix = [eur for _, eur in paliers]
    assert volumes == sorted(set(volumes))
    assert prix == sorted(set(prix))


def test_les_deux_offres_ont_une_grille_complete():
    """Plus d'alerte « grille incomplete » a l'ecran : les deux sont sourcees."""
    for offre in batterie_virtuelle.offres().values():
        assert offre.grille_complete, offre.code


def test_une_seule_offre_est_recommandee_et_c_est_le_sur_mesure():
    """La doctrine vit dans les donnees, pas dans l'ordre d'un dictionnaire.

    Deux offres marquees « recommandee » rendraient le choix par defaut arbitraire.
    """
    recommandees = [o.code for o in batterie_virtuelle.offres().values() if o.recommandee]
    assert recommandees == ["mysmartbattery"]


def test_le_sur_mesure_ne_facture_pas_le_transport_restitue():
    """La difference qui decide du conseil : l'abonnement du palier est tout compris."""
    offres = batterie_virtuelle.offres()
    assert offres["mysmartbattery"].cout_restitution_eur_kwh == 0.0
    assert offres["mybattery"].cout_restitution_eur_kwh > 0.0


def test_le_palier_retenu_couvre_le_volume_a_stocker():
    """On ne loue jamais moins que ce qu'on stocke, tant qu'un palier existe au-dessus."""
    sur_mesure = batterie_virtuelle.offres()["mysmartbattery"]
    for volume in (1, 20, 21, 150, 950, 2999, 9999):
        kwh, _ = sur_mesure.palier_pour(volume)
        assert kwh >= volume, volume


def test_au_dela_du_dernier_palier_on_retombe_sur_le_plus_grand():
    """10 000 kWh est le plafond de la grille : au-dela, le chiffrage est un plancher."""
    sur_mesure = batterie_virtuelle.offres()["mysmartbattery"]
    kwh, eur = sur_mesure.palier_pour(50_000)
    assert (kwh, eur) == (10_000, 214.99)


# --- Le palier est une reserve, et il se choisit au moins-disant -------------------

def _annee(surplus_midi: float, besoin_soir: float) -> tuple[list[float], list[float]]:
    """Une annee ou le surplus du midi paie le besoin du soir, tous les jours.

    Cas volontairement extreme : le credit ne depasse jamais la valeur d'une journee,
    alors qu'il passe des milliers de kWh dans l'annee. C'est exactement la situation
    que l'ancien modele facturait au prix fort.
    """
    besoin_h: list[float] = []
    surplus_h: list[float] = []
    for _ in range(365):
        for heure in range(24):
            besoin_h.append(besoin_soir if heure == 20 else 0.0)
            surplus_h.append(surplus_midi if heure == 12 else 0.0)
    return besoin_h, surplus_h


def test_le_palier_se_mesure_sur_la_reserve_detenue_pas_sur_le_volume_annuel():
    """8 kWh detenus, 2 920 kWh passes dans l'annee : on loue 20 kWh, pas 3 000.

    C'est LE test de non-regression de cette correction. Avant le 28/09/2026, le moteur
    choisissait le palier a partir du volume stocke sur l'annee et facturait 1 080 EUR
    la ou la grille demande 156 EUR.
    """
    sur_mesure = batterie_virtuelle.offres()["mysmartbattery"]
    besoin_h, surplus_h = _annee(surplus_midi=8.0, besoin_soir=8.0)
    bilan = batterie_virtuelle.simuler(
        sur_mesure, besoin_h, surplus_h, kwc=6.0, prix_achat_kwh=0.20, prix_revente_kwh=0.04)

    assert bilan["stocke_kwh"] == pytest.approx(2920.0)
    assert bilan["credit_maxi_kwh"] <= 8.0
    assert bilan["palier_kwh"] == 20
    assert bilan["abonnement_annuel_eur"] == pytest.approx(12.99 * 12)


def test_on_ne_loue_jamais_plus_grand_que_le_palier_qui_couvre_la_pointe():
    """Au-dela, l'energie ne bouge plus d'un kWh et seul l'abonnement grimpe."""
    sur_mesure = batterie_virtuelle.offres()["mysmartbattery"]
    besoin_h, surplus_h = _annee(surplus_midi=30.0, besoin_soir=10.0)
    bilan = batterie_virtuelle.simuler(
        sur_mesure, besoin_h, surplus_h, kwc=6.0, prix_achat_kwh=0.20, prix_revente_kwh=0.04)

    libre = batterie_virtuelle._passage(besoin_h, surplus_h, None)
    couvrant = sur_mesure.palier_pour(libre["credit_maxi_kwh"])
    assert bilan["palier_kwh"] <= couvrant[0]


def test_un_palier_impose_est_respecte_et_plafonne_vraiment_le_credit():
    """Quand l'utilisateur choisit sa reserve, le moteur ne la corrige pas en douce —
    et le surplus qui ne rentre plus est REFUSE, donc reparti a l'injection."""
    sur_mesure = batterie_virtuelle.offres()["mysmartbattery"]
    besoin_h, surplus_h = _annee(surplus_midi=30.0, besoin_soir=10.0)
    bilan = batterie_virtuelle.simuler(
        sur_mesure, besoin_h, surplus_h, kwc=6.0, palier_force=100,
        prix_achat_kwh=0.20, prix_revente_kwh=0.04)

    assert bilan["palier_kwh"] == 100
    assert bilan["credit_maxi_kwh"] <= 100.0
    assert bilan["refuse_kwh"] > 0


def test_seul_le_sur_mesure_demande_du_materiel():
    """Le coffret MyLight n'existe que d'un cote. Il entre dans l'investissement."""
    offres = batterie_virtuelle.offres()
    assert offres["mysmartbattery"].materiel_eur > 0
    assert offres["mybattery"].materiel_eur == 0.0
