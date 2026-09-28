"""Le contrat du simulateur — ce qui ne doit jamais cesser d'être vrai.

Ces tests ne vérifient pas des valeurs (elles bougeront avec les calibrages) mais des
PROPRIÉTÉS : l'énergie ne se crée pas, plus de panneaux produisent plus, une règle de TVA
s'applique, et la suggestion affichée ne contredit pas la recommandation. Un test qui
gêne signale un problème de conception, pas un test à réécrire.
"""

import asyncio

import pytest

from app.core.config import settings
from app.services import simu_conso, simu_engine, simu_options, simu_pv
from app.services.simu_types import Panneaux, Stockage
from tests.conftest import SERIE_1KWC, config_type, maison_type, production_ref

TOLERANCE = 0.5  # kWh sur l'année : les arrondis d'affichage, rien de plus


def _resultat(config, detail=True):
    profil = simu_conso.construire(config.maison)
    ref = production_ref(config.panneaux.nb_panneaux, config.panneaux.nb_panneaux_carport)
    return simu_engine.calculer(config, profil, ref["total_h"], detail=detail)


# --- Bilans fermés ---------------------------------------------------------------

@pytest.mark.parametrize("stockage", [
    {},
    {"pilotage": True},
    {"nb_packs": 2},
    {"batterie_virtuelle": "mybattery"},
    {"nb_packs": 2, "batterie_virtuelle": "mybattery", "pilotage": True},
])
def test_bilan_production_se_ferme(stockage):
    """production = autoconso directe + charge batterie + injecté + écrêté + stocké virtuel."""
    a = _resultat(config_type(**stockage))["bilan_annuel"]
    somme = a["direct"] + a["charge"] + a["injecte"] + a["ecrete"] + a["stocke_virtuel"]
    assert abs(a["production"] - somme) < TOLERANCE, f"{a['production']} != {somme}"


@pytest.mark.parametrize("stockage", [
    {},
    {"pilotage": True},
    {"nb_packs": 2},
    {"batterie_virtuelle": "mybattery"},
    {"nb_packs": 2, "batterie_virtuelle": "mybattery", "pilotage": True},
])
def test_bilan_consommation_se_ferme(stockage):
    """consommation = autoconso directe + décharge + restitution virtuelle + acheté."""
    a = _resultat(config_type(**stockage))["bilan_annuel"]
    somme = a["direct"] + a["decharge"] + a["restitue_virtuel"] + a["achat"]
    assert abs(a["consommation"] - somme) < TOLERANCE, f"{a['consommation']} != {somme}"


def test_les_bilans_mensuels_somment_a_l_annuel():
    resultat = _resultat(config_type(nb_packs=1, pilotage=True))
    annuel = resultat["bilan_annuel"]
    for champ in ("production", "consommation", "direct", "achat"):
        somme = sum(mois[champ] for mois in resultat["bilan_mensuel"])
        assert abs(annuel[champ] - somme) < TOLERANCE, champ


# --- Monotonie -------------------------------------------------------------------

def test_plus_de_panneaux_produit_plus():
    precedent = 0.0
    for nb in (4, 8, 12, 20):
        production = _resultat(config_type(nb_panneaux=nb), detail=False)["bilan_annuel"]["production"]
        assert production > precedent, f"{nb} panneaux ne produisent pas plus que {precedent}"
        precedent = production


def test_le_pilotage_ne_degrade_jamais_l_autoconsommation():
    sans = _resultat(config_type(pilotage=False), detail=False)["bilan_annuel"]
    avec = _resultat(config_type(pilotage=True), detail=False)["bilan_annuel"]
    assert avec["direct"] >= sans["direct"]
    assert avec["achat"] <= sans["achat"] + TOLERANCE


def test_la_batterie_augmente_l_autoconsommation_totale():
    def autoconso(**kw):
        a = _resultat(config_type(**kw), detail=False)["bilan_annuel"]
        return a["direct"] + a["decharge"]
    assert autoconso(nb_packs=2) > autoconso(nb_packs=0)


# --- Mise à l'échelle : une série de 1 kWc suffit --------------------------------

def test_la_serie_1kwc_multipliee_vaut_un_appel_direct(pvgis_factice):
    """Toute puissance se déduit de la série de 1 kWc — c'est ce qui évite de rappeler PVGIS."""
    from app.services.simu_types import Lieu
    lieu = Lieu(lat=43.3012, lon=5.4013)

    async def scenario():
        serie = await simu_pv.serie_1kwc(lat=lieu.lat, lon=lieu.lon, angle=30, aspect=0, loss=14.0)
        directe = await simu_pv.pvgis.production_series_hourly(
            lat=lieu.lat, lon=lieu.lon, peakpower=6.0, angle=30, aspect=0, loss=14.0)
        return serie, directe

    serie, directe = asyncio.run(scenario())
    mise_a_l_echelle = [v * 6.0 for v in serie]
    assert max(abs(a - b) for a, b in zip(mise_a_l_echelle, directe)) < 1e-9


def test_pvgis_n_est_appele_qu_une_fois_par_lieu(pvgis_factice):
    """Ajouter des panneaux ne doit déclencher AUCUN appel sortant supplémentaire."""
    from app.services.simu_types import Lieu
    lieu = Lieu(lat=43.3012, lon=5.4013)

    async def scenario():
        for nb in (6, 10, 14, 18):
            await simu_pv.production(lieu, Panneaux(nb_panneaux=nb, orientation="sud",
                                                    inclinaison=30, ombrage="aucun"))

    asyncio.run(scenario())
    assert len(pvgis_factice) == 1, f"{len(pvgis_factice)} appels PVGIS au lieu d'un seul"


def test_les_coordonnees_voisines_partagent_le_cache(pvgis_factice):
    """Deux adresses de la même commune ne doivent pas provoquer deux appels."""
    from app.services.simu_types import Lieu

    async def scenario():
        for lat, lon in ((43.3001, 5.4002), (43.3009, 5.3998), (43.2995, 5.4005)):
            await simu_pv.production(Lieu(lat=lat, lon=lon),
                                     Panneaux(nb_panneaux=10, orientation="sud",
                                              inclinaison=30, ombrage="aucun"))

    asyncio.run(scenario())
    assert len(pvgis_factice) == 1


def test_est_ouest_demande_deux_series_et_produit_moins_que_plein_sud(pvgis_factice):
    from app.services.simu_types import Lieu
    lieu = Lieu(lat=43.30, lon=5.40)

    async def scenario():
        sud = await simu_pv.production(lieu, Panneaux(nb_panneaux=10, orientation="sud",
                                                      inclinaison=30, ombrage="aucun"))
        est_ouest = await simu_pv.production(lieu, Panneaux(nb_panneaux=10, orientation="est_ouest",
                                                           inclinaison=30, ombrage="aucun"))
        return sud, est_ouest

    sud, est_ouest = asyncio.run(scenario())
    aspects = {a["aspect"] for a in pvgis_factice}
    assert aspects == {0, -90, 90}, aspects
    # La série factice ne dépend pas de l'azimut : on vérifie le câblage, pas la physique.
    assert est_ouest["kwc_total"] == sud["kwc_total"]


# --- Règles --------------------------------------------------------------------

def test_tva_reduite_sous_le_seuil_sans_batterie():
    invest = _resultat(config_type(nb_panneaux=14), detail=False)["investissement"]
    assert invest["tva_pct"] == settings.simu_tva_reduite_pct


def test_une_batterie_physique_fait_basculer_tout_le_projet_a_20():
    invest = _resultat(config_type(nb_panneaux=14, nb_packs=1), detail=False)["investissement"]
    assert invest["tva_pct"] == settings.simu_tva_pleine_pct
    assert "batterie" in invest["tva_raison"].lower()


def test_au_dela_du_seuil_de_puissance_la_tva_est_pleine():
    """20 panneaux de 500 Wc = 10 kWc, au-dessus des 9 kWc."""
    invest = _resultat(config_type(nb_panneaux=20), detail=False)["investissement"]
    assert invest["tva_pct"] == settings.simu_tva_pleine_pct


def test_la_batterie_virtuelle_ne_change_pas_la_tva():
    invest = _resultat(config_type(nb_panneaux=14, batterie_virtuelle="mybattery"),
                       detail=False)["investissement"]
    assert invest["tva_pct"] == settings.simu_tva_reduite_pct


def _petit_foyer(raccordement: str):
    return maison_type(conso_connue_kwh_an=2500, raccordement=raccordement,
                       chauffage="gaz", ecs="gaz")


def test_le_monophase_ecrete_l_injection_a_6_kva():
    """La physique : en monophasé le surplus bute sur le plafond, en triphasé non."""
    mono = _resultat(config_type(nb_panneaux=24, maison=_petit_foyer("monophase")), detail=False)
    triphase = _resultat(config_type(nb_panneaux=24, maison=_petit_foyer("triphase")), detail=False)

    assert mono["bilan_annuel"]["ecrete"] > 0
    assert triphase["bilan_annuel"]["ecrete"] == 0


def test_un_ecretage_negligeable_n_alerte_pas():
    """Et c'est le point : ce test demandait l'inverse jusqu'au 28/09/2026.

    L'alerte se declenchait des qu'un seul kWh etait ecrete — et meme, par une seconde
    regle, des que la puissance POSEE depassait le plafond, sans qu'un seul kWh ne soit
    perdu. Stephane l'a signale sur un cas reel : un 9 kWc plein sud bien incline culmine
    vers 7,8 kW a midi en juin, dont le talon de la maison (300 a 500 W) et les usages du
    moment mangent une bonne part. Il ne sort quasiment jamais plus de 6 kVA.

    Mesure ici : 12 kWc sur un foyer de 2 500 kWh perd 142 kWh par an, soit 1 % de la
    production, environ 6 EUR. Un bandeau rouge pour cela use l'attention du lecteur, qui
    finit par ne plus lire les alertes qui comptent.
    """
    resultat = _resultat(config_type(nb_panneaux=24, maison=_petit_foyer("monophase")),
                         detail=False)
    annuel = resultat["bilan_annuel"]
    part = 100 * annuel["ecrete"] / annuel["production"]

    assert 0 < part < settings.simu_ecretage_alerte_pct
    assert not any("plafonn" in a["texte"] for a in resultat["alertes"])


def test_un_ecretage_qui_pese_alerte_toujours():
    """Au-dela du seuil, l'avertissement reste — c'est la que le triphase se chiffre."""
    resultat = _resultat(config_type(nb_panneaux=32, maison=_petit_foyer("monophase")),
                         detail=False)
    annuel = resultat["bilan_annuel"]
    part = 100 * annuel["ecrete"] / annuel["production"]

    assert part >= settings.simu_ecretage_alerte_pct
    assert any("plafonn" in a["texte"] for a in resultat["alertes"])


def test_aucune_alerte_sur_la_seule_puissance_posee():
    """9 kWc en monophase : rien n'est ecrete, donc rien ne doit crier.

    C'est le cas exact de la capture d'ecran du 28/09/2026 : deux bandeaux rouges pour
    zero kWh perdu.
    """
    resultat = _resultat(config_type(nb_panneaux=18, maison=_petit_foyer("monophase")),
                         detail=False)

    assert resultat["bilan_annuel"]["ecrete"] == 0
    assert not any(a["niveau"] == "attention" for a in resultat["alertes"])


def test_un_raccordement_inconnu_est_traite_en_monophase_et_le_dit():
    resultat = _resultat(config_type(nb_panneaux=24, maison=maison_type(
        conso_connue_kwh_an=2500, raccordement="inconnu", chauffage="gaz", ecs="gaz")), detail=False)
    assert resultat["bilan_annuel"]["ecrete"] > 0
    assert any("inconnu" in a["texte"].lower() for a in resultat["alertes"])


def test_l_ecretage_n_est_ni_vendu_ni_consomme():
    """L'énergie écrêtée est perdue : elle ne doit apparaître dans aucun flux valorisé."""
    a = _resultat(config_type(nb_panneaux=24, maison=maison_type(
        conso_connue_kwh_an=2500, raccordement="monophase", chauffage="gaz", ecs="gaz")),
        detail=False)["bilan_annuel"]
    assert a["ecrete"] > 0
    somme = a["direct"] + a["charge"] + a["injecte"] + a["ecrete"] + a["stocke_virtuel"]
    assert abs(a["production"] - somme) < TOLERANCE


# --- Consommation ----------------------------------------------------------------

def test_la_conso_connue_est_respectee_et_les_ajouts_s_additionnent():
    """Un équipement déjà là façonne la courbe ; un équipement ajouté s'additionne."""
    from app.services.simu_types import Voiture
    deja = simu_conso.construire(maison_type(conso_connue_kwh_an=9000))
    assert abs(deja.annuel_kwh - 9000) < 1.0

    ajoutee = simu_conso.construire(maison_type(
        conso_connue_kwh_an=9000,
        voiture=Voiture(present=True, deja_installe=False, km_an=12000, recharge="nuit")))
    attendu = 9000 + 12000 * settings.simu_conso_ve_kwh_100km / 100
    assert abs(ajoutee.annuel_kwh - attendu) < 1.0
    assert "voiture" in ajoutee.ajoutees


def test_la_courbe_est_deterministe():
    a = simu_conso.construire(maison_type())
    b = simu_conso.construire(maison_type())
    assert a.total_h == b.total_h


def test_une_residence_secondaire_consomme_moins_hors_saison():
    principale = simu_conso.construire(maison_type(conso_connue_kwh_an=None))
    secondaire = simu_conso.construire(maison_type(
        conso_connue_kwh_an=None, residence_secondaire=True, mois_occupation=(7, 8)))
    assert secondaire.annuel_kwh < principale.annuel_kwh


def test_le_chauffage_non_electrique_ne_consomme_pas_d_electricite():
    profil = simu_conso.construire(maison_type(chauffage="gaz", conso_connue_kwh_an=None))
    assert profil.detail_kwh["chauffage"] == 0.0


# --- Cohérence options / prochaine étape ----------------------------------------

def _options(config):
    profil = simu_conso.construire(config.maison)
    ref = production_ref(config.panneaux.nb_panneaux, config.panneaux.nb_panneaux_carport)
    return simu_options.calculer_options(config, profil, ref)


def test_la_prochaine_etape_ne_contredit_pas_la_recommandation():
    """Si elle propose des panneaux, c'est la taille de l'option recommandée, pas une autre."""
    resultat = _options(config_type(nb_panneaux=4))
    etape = resultat["prochaine_etape"]
    assert etape is not None
    if "nb_panneaux" in etape["appliquer"]:
        recommandee = next(o for o in resultat["options"] if o["code"] == resultat["recommandee"])
        assert etape["appliquer"]["nb_panneaux"] == recommandee["nb_panneaux"]


def test_les_trois_options_sont_toujours_chiffrees():
    resultat = _options(config_type(nb_panneaux=10))
    codes = {o["code"] for o in resultat["options"]}
    assert codes == {"batterie_virtuelle", "batterie_physique", "pilotage"}
    for option in resultat["options"]:
        assert option["investissement_eur"] > 0
        assert option["nb_panneaux"] > 0


def test_la_recommandation_est_le_meilleur_gain_sur_25_ans():
    resultat = _options(config_type(nb_panneaux=10))
    meilleure = max(resultat["options"], key=lambda o: o["gain_net_25_ans_eur"])
    assert resultat["recommandee"] == meilleure["code"]


def test_le_besoin_de_secours_ne_maquille_pas_la_rentabilite():
    """Le secours change le discours, jamais les chiffres."""
    sans = _options(config_type(nb_panneaux=10, maison=maison_type(besoin_secours=False)))
    avec = _options(config_type(nb_panneaux=10, maison=maison_type(besoin_secours=True)))

    def batterie(resultat):
        return next(o for o in resultat["options"] if o["code"] == "batterie_physique")

    assert batterie(sans)["gain_net_25_ans_eur"] == batterie(avec)["gain_net_25_ans_eur"]
    assert batterie(sans)["investissement_eur"] == batterie(avec)["investissement_eur"]
    assert batterie(avec)["note_secours"] is not None
    assert batterie(sans)["note_secours"] is None


def test_la_prochaine_etape_est_toujours_un_gain():
    etape = _options(config_type(nb_panneaux=6))["prochaine_etape"]
    assert etape is None or etape["gain_annuel_eur"] > 0


def test_appliquer_la_prochaine_etape_ameliore_vraiment():
    """La suggestion doit tenir sa promesse quand on l'applique pour de vrai."""
    config = config_type(nb_panneaux=6)
    resultat = _options(config)
    etape = resultat["prochaine_etape"]
    assert etape is not None

    avant = _resultat(config, detail=False)["indicateurs"]["economie_1re_annee_eur"]
    appliquer = etape["appliquer"]
    apres_config = config
    if "nb_panneaux" in appliquer:
        apres_config = apres_config.avec(panneaux=Panneaux(
            nb_panneaux=appliquer["nb_panneaux"], orientation=config.panneaux.orientation,
            inclinaison=config.panneaux.inclinaison, ombrage=config.panneaux.ombrage))
    if "pilotage" in appliquer or "batterie_virtuelle" in appliquer or "nb_packs" in appliquer:
        apres_config = apres_config.avec(stockage=Stockage(
            nb_packs=appliquer.get("nb_packs", config.stockage.nb_packs),
            batterie_virtuelle=appliquer.get("batterie_virtuelle", config.stockage.batterie_virtuelle),
            pilotage=appliquer.get("pilotage", config.stockage.pilotage)))

    apres = _resultat(apres_config, detail=False)["indicateurs"]["economie_1re_annee_eur"]
    assert apres > avant


# --- Objectifs et hypothèses -----------------------------------------------------

def test_les_objectifs_sont_coches_d_apres_le_resultat():
    resultat = _options(config_type(nb_panneaux=14))
    codes = {o["code"] for o in resultat["objectifs"]}
    assert codes == {"autonomie", "facture", "retour", "tva", "pilotage"}


def test_les_hypotheses_portent_toutes_un_statut():
    for hypothese in simu_engine.hypotheses():
        assert hypothese["statut"], hypothese["libelle"]
        assert hypothese["valeur"]


# --- Stockage par inertie ---------------------------------------------------------

def test_l_inertie_ajoute_de_la_capacite_comme_une_batterie():
    """10 kWh enterres valent 10 kWh en armoire : le moteur ne les distingue pas."""
    sans = _resultat(config_type(nb_panneaux=14), detail=False)
    avec = _resultat(config_type(nb_panneaux=14, inertie=True), detail=False)

    assert avec["bilan_annuel"]["charge"] > sans["bilan_annuel"]["charge"]
    assert avec["indicateurs"]["autonomie_pct"] > sans["indicateurs"]["autonomie_pct"]
    assert avec["stockage"]["inertie"]["presente"] is True


def test_l_inertie_ne_se_remplace_pas_dans_les_25_ans():
    """C'est LA difference economique avec le lithium, et elle doit se voir.

    Garantie 40 ans contre 15 : a capacite egale et economie annuelle egale, le lithium
    porte un remplacement en cours d'etude, l'inertie non. Son temps de retour est donc
    meilleur, alors meme qu'elle coute plus cher a l'achat.
    """
    inertie = _resultat(config_type(nb_panneaux=14, inertie=True), detail=False)
    # 2 packs = 10 kWh, la meme capacite utile.
    lithium = _resultat(config_type(nb_panneaux=14, nb_packs=2), detail=False)

    assert inertie["investissement"]["total_eur"] > lithium["investissement"]["total_eur"]
    assert inertie["economie"]["temps_retour_ans"] < lithium["economie"]["temps_retour_ans"]


def test_l_inertie_fait_basculer_la_tva_comme_une_batterie():
    """Hypothese prudente, signalee a l'ecran et dans la config : a confirmer."""
    resultat = _resultat(config_type(nb_panneaux=14, inertie=True), detail=False)
    assert resultat["investissement"]["tva_pct"] == settings.simu_tva_pleine_pct
