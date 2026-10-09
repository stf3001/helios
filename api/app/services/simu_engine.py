"""Moteur horaire du simulateur « maison + équipements » — étape 1.

Une seule passe sur 8 760 heures produit tout : autonomie, facture, écrêtage, bilans
mensuels, journées moyennes. Les montants sur 25 ans en découlent.

DÉTERMINISTE, sans LLM, sans réseau (règle projet, doc 07 §6). Toutes les hypothèses
viennent de `config.py` et ressortent dans `hypotheses` pour être affichées.

Deux invariants que les tests vérifient et qu'il ne faut jamais casser :
  production   = autoconsommation directe + charge batterie + injecté + écrêté + stocké virtuel
  consommation = autoconsommation directe + décharge + restitution virtuelle + acheté
Si un bilan cesse de se fermer, c'est que de l'énergie est créée ou perdue quelque part.
"""

from dataclasses import dataclass, field

from app.core.config import settings
from app.services import batterie_virtuelle, eolien, simu_conso, solar_engine
from app.services.simu_conso import HEURES, ProfilConso
from app.services.simu_types import Configuration

# Version du moteur, enregistree avec chaque etude : les hypotheses evoluent, une etude
# relue plus tard doit dire avec quoi elle a ete produite.
VERSION_MOTEUR = "simu-1"

SAISONS = {
    "hiver": (12, 1, 2),
    "printemps": (3, 4, 5),
    "ete": (6, 7, 8),
    "automne": (9, 10, 11),
}


def prix_kwh(puissance_kva: int) -> float:
    for kva, prix in sorted(settings.simu_prix_kwh_par_kva):
        if puissance_kva <= kva:
            return prix
    return sorted(settings.simu_prix_kwh_par_kva)[-1][1]


def abonnement_annuel_eur(puissance_kva: int) -> float:
    grille = sorted(settings.simu_abonnement_eur_mois_par_kva)
    for kva, eur in grille:
        if puissance_kva <= kva:
            return round(eur * 12, 2)
    return round(grille[-1][1] * 12, 2)


def _piloter(total_h: list[float], pilotable_h: list[float], prod_h: list[float]) -> list[float]:
    """Décale ballon, filtration et recharge vers les heures de surplus, jour par jour.

    L'énergie déplacée est conservée exactement (on ne consomme pas moins, on consomme
    au bon moment). Si le placement d'origine capte déjà plus de solaire que le nouveau,
    on garde l'original : le pilotage ne doit jamais dégrader la situation.
    """
    non_pilotable = [t - p for t, p in zip(total_h, pilotable_h)]
    nouveau = list(total_h)

    for jour in range(365):
        debut, fin = jour * 24, jour * 24 + 24
        besoin = sum(pilotable_h[debut:fin])
        if besoin <= 0:
            continue
        capacite = [max(0.0, prod_h[h] - non_pilotable[h]) for h in range(debut, fin)]
        total_capacite = sum(capacite)
        if total_capacite <= 0:
            continue

        a_placer = min(besoin, total_capacite)
        reste = besoin - a_placer
        propose = [
            c / total_capacite * a_placer + (pilotable_h[debut + i] / besoin) * reste
            for i, c in enumerate(capacite)
        ]

        gain_origine = sum(min(pilotable_h[debut + i], capacite[i]) for i in range(24))
        gain_propose = sum(min(propose[i], capacite[i]) for i in range(24))
        if gain_propose <= gain_origine:
            continue
        for i in range(24):
            nouveau[debut + i] = non_pilotable[debut + i] + propose[i]

    return nouveau


@dataclass
class BilanHoraire:
    direct_h: list[float]
    charge_h: list[float]
    decharge_h: list[float]
    injecte_h: list[float]
    ecrete_h: list[float]
    stocke_virtuel_h: list[float]
    restitue_virtuel_h: list[float]
    achat_h: list[float]
    conso_h: list[float]
    prod_h: list[float]
    #: Ce que la banque virtuelle a renvoyé, tel quel. Il contient la pointe de crédit et
    #: le palier retenu, que personne ne peut retrouver à partir des seuls totaux annuels.
    virtuel: dict | None = None
    #: Machine à eau en mode « solaire seul » : ce qu'elle a pu consommer et produire.
    eau_kwh_h: list[float] = field(default_factory=list)
    eau_litres_h: list[float] = field(default_factory=list)


def _simuler_horaire(conso_h: list[float], prod_h: list[float], config: Configuration,
                     eau_potentiel_kwh: list[float] | None = None,
                     eau_potentiel_litres: list[float] | None = None) -> BilanHoraire:
    """La passe horaire : autoconsommation, batterie, écrêtage, batterie virtuelle."""
    # Deux stockages possibles, et ils s'additionnent : des packs lithium qu'on empile, et
    # un stockage par inertie qu'on enterre (un seul). Le moteur ne les distingue pas au
    # moment de charger et decharger — un kWh est un kWh. Ils ne different qu'au prix, a la
    # duree de vie et a la fiscalite.
    packs = max(config.stockage.nb_packs, 0)
    capacite = packs * settings.simu_batterie_pack_kwh
    puissance = packs * settings.simu_batterie_pack_kw
    if config.stockage.inertie:
        capacite += settings.simu_inertie_capacite_kwh
        puissance += settings.simu_inertie_puissance_kw
    rendement = settings.autoconso_battery_efficiency

    # Monophasé (« inconnu » compte comme monophasé, et c'est signalé) : l'injection est
    # plafonnée. Au-delà, l'énergie n'est ni vendue ni consommée — elle est perdue.
    mono = config.maison.raccordement in ("monophase", "inconnu")
    plafond = settings.simu_injection_max_kva_mono if mono else None

    soc = 0.0
    direct_h, charge_h, decharge_h = [], [], []
    injectable_h, ecrete_h, besoin_h = [], [], []
    #: Ce que la machine a eau a reellement consomme et produit, heure par heure. En marche
    #: continue elle est deja dans `conso_h` et ces listes restent a zero ; c'est le mode
    #: « sur solaire seul » qui les remplit, puisque lui seul module la marche.
    eau_kwh_h: list[float] = []
    eau_litres_h: list[float] = []

    for i, (conso, prod) in enumerate(zip(conso_h, prod_h)):
        direct = min(conso, prod)
        surplus = prod - direct
        besoin = conso - direct

        # La machine a eau sur solaire seul : elle se sert AVANT la batterie. Elle consomme
        # sur-le-champ, et stocker pour faire de l'eau plus tard ajouterait les pertes de la
        # batterie a une operation deja couteuse en energie. Ce qu'elle laisse continue son
        # chemin : batterie, puis injection.
        if eau_potentiel_kwh is not None:
            besoin_eau = eau_potentiel_kwh[i]
            pris = min(surplus, besoin_eau) if besoin_eau > 0 else 0.0
            surplus -= pris
            eau_kwh_h.append(pris)
            eau_litres_h.append(
                eau_potentiel_litres[i] * (pris / besoin_eau) if besoin_eau > 0 else 0.0)

        charge = min(surplus, puissance, max(capacite - soc, 0.0)) if (capacite and surplus > 0) else 0.0
        soc += charge * rendement
        surplus -= charge

        decharge = min(besoin, puissance, soc) if (capacite and besoin > 0) else 0.0
        soc -= decharge
        besoin -= decharge

        if plafond is not None and surplus > plafond:
            ecrete = surplus - plafond
            surplus = plafond
        else:
            ecrete = 0.0

        direct_h.append(direct)
        charge_h.append(charge)
        decharge_h.append(decharge)
        injectable_h.append(surplus)
        ecrete_h.append(ecrete)
        besoin_h.append(besoin)

    # Batterie virtuelle : le surplus n'est plus injecté, il est mis en banque.
    offre_code = config.stockage.batterie_virtuelle
    offre = batterie_virtuelle.offres().get(offre_code) if offre_code else None
    if offre is not None:
        kwc = _kwc_total(config)
        # Les deux prix servent à choisir le palier : ce qui sort d'une petite réserve
        # n'est pas perdu, il se vend. Sans eux, la banque ne saurait pas arbitrer.
        virtuel = batterie_virtuelle.simuler(
            offre, besoin_h, injectable_h, kwc=kwc,
            palier_force=config.stockage.palier_virtuel_kwh,
            prix_achat_kwh=prix_kwh(config.maison.puissance_souscrite_kva),
            prix_revente_kwh=settings.solar_prix_revente_eur_kwh,
        )
        achat_h = virtuel["achat_h"]
        restitue_h = [b - a for b, a in zip(besoin_h, achat_h)]
        # Ce que la banque a refusé (plafond de crédit) repart à l'injection classique.
        stocke_h = [i for i in injectable_h]
        if virtuel["refuse_kwh"] <= 0:
            injecte_h = [0.0] * HEURES
        else:
            # Répartition au prorata : le détail à l'heure près n'ajoute rien à la décision.
            part = virtuel["refuse_kwh"] / sum(injectable_h) if sum(injectable_h) else 0.0
            injecte_h = [i * part for i in injectable_h]
            stocke_h = [i * (1 - part) for i in injectable_h]
    else:
        achat_h = besoin_h
        restitue_h = [0.0] * HEURES
        stocke_h = [0.0] * HEURES
        injecte_h = injectable_h

    return BilanHoraire(
        direct_h=direct_h, charge_h=charge_h, decharge_h=decharge_h,
        injecte_h=injecte_h, ecrete_h=ecrete_h,
        stocke_virtuel_h=stocke_h, restitue_virtuel_h=restitue_h,
        achat_h=achat_h, conso_h=conso_h, prod_h=prod_h,
        virtuel=virtuel if offre is not None else None,
        eau_kwh_h=eau_kwh_h, eau_litres_h=eau_litres_h,
    )


def _inertie_ttc() -> float:
    """Prix pose du stockage par inertie, TVA comprise.

    Son taux lui est propre (5,5 % depuis le 06/10/2026) et n'est PAS celui que
    `investissement()` applique au reste du projet : ajouter de l'inertie fait toujours
    basculer le photovoltaique a 20 %, hypothese prudente non tranchee (cf. `config.py`).
    """
    return settings.simu_inertie_cout_ht_eur * (1 + settings.simu_inertie_tva_pct / 100)


def _kwc_total(config: Configuration) -> float:
    return (config.panneaux.nb_panneaux + config.panneaux.nb_panneaux_carport) * settings.simu_panneau_wc / 1000


def investissement(config: Configuration) -> dict:
    """Coût du projet, TVA comprise, avec le détail de la règle appliquée.

    La grille de `config.py` est une grille de DEVIS, donc TTC au taux réduit : on la
    ramène hors taxes avant d'appliquer le taux réellement dû. Une batterie physique ou
    plus de 9 kWc font basculer TOUT le projet à 20 % — c'est la règle, pas un réglage.
    """
    kwc = _kwc_total(config)
    nb_carport = config.panneaux.nb_panneaux_carport
    packs = max(config.stockage.nb_packs, 0)

    taux_reduit = settings.simu_tva_reduite_pct
    taux_plein = settings.simu_tva_pleine_pct
    # Un stockage par inertie reste un stockage : l'outil suppose qu'il fait basculer le
    # projet a 20 % de TVA comme le lithium. Hypothese prudente et signalee (cf. config).
    batterie_presente = packs > 0 or config.stockage.inertie
    hors_criteres = kwc > settings.simu_tva_seuil_kwc or batterie_presente
    taux = taux_plein if hors_criteres else taux_reduit

    pv_ttc_devis = solar_engine.cout_installation_eur(kwc) if kwc > 0 else 0.0
    pv_ht = pv_ttc_devis / (1 + taux_reduit / 100)
    pv_ttc = pv_ht * (1 + taux / 100)

    carport_ht = nb_carport * settings.simu_carport_cout_par_panneau_eur
    carport_ttc = carport_ht * (1 + settings.simu_carport_tva_pct / 100)

    batterie_ht = packs * settings.simu_batterie_pack_kwh * settings.simu_batterie_cout_par_kwh_eur / (
        1 + taux_plein / 100
    )
    batterie_ttc = batterie_ht * (1 + taux_plein / 100)

    inertie_ttc = _inertie_ttc() if config.stockage.inertie else 0.0

    # L'eolienne est chiffree TTC par EOLIA, TVA 20 % comprise. Elle ne change PAS le
    # taux du photovoltaique : ce sont deux installations distinctes, et la condition
    # des 5,5 % porte sur l'installation solaire elle-meme. A confirmer aupres d'un
    # installateur avant d'en faire un argument.
    eolien_ttc = float(eolien.cout_ttc_eur(config.eolien.kwc)) if config.eolien.kwc > 0 else 0.0

    offre_code = config.stockage.batterie_virtuelle
    offre = batterie_virtuelle.offres().get(offre_code) if offre_code else None
    activation = offre.activation_eur if offre else 0.0
    # Le coffret du stockage sur-mesure : du matériel posé chez le client, donc de
    # l'investissement. Le stockage illimité n'en demande aucun et reste à zéro.
    materiel_virtuel = offre.materiel_eur if offre else 0.0

    raison = (
        "Batterie physique dans le projet : TVA 20 % sur l'ensemble."
        if batterie_presente
        else f"Plus de {settings.simu_tva_seuil_kwc:g} kWc : TVA 20 % sur l'ensemble."
        if kwc > settings.simu_tva_seuil_kwc
        else "TVA 5,5 % (≤ 9 kWc, sans batterie physique, sous réserve des autres conditions)."
    )

    return {
        "panneaux_eur": round(pv_ttc),
        "carport_eur": round(carport_ttc),
        "batterie_eur": round(batterie_ttc),
        "inertie_eur": round(inertie_ttc),
        "eolien_eur": round(eolien_ttc),
        "activation_virtuelle_eur": round(activation),
        "materiel_virtuel_eur": round(materiel_virtuel),
        "total_eur": round(pv_ttc + carport_ttc + batterie_ttc + inertie_ttc + eolien_ttc
                           + activation + materiel_virtuel),
        "tva_pct": taux,
        "tva_raison": raison,
    }


def _bornes_mois() -> list[tuple[int, int]]:
    """(première heure, dernière heure exclue) de chaque mois — les mois sont contigus."""
    bornes, debut = [], 0
    for mois in range(1, 13):
        duree = sum(1 for m, _, _ in simu_conso.CALENDRIER if m == mois)
        bornes.append((debut, debut + duree))
        debut += duree
    return bornes


BORNES_MOIS = _bornes_mois()


def _agreger(bilan: BilanHoraire, detail: bool = True) -> dict:
    """Bilans annuel, mensuel et journées moyennes par saison.

    Tout passe par des TRANCHES de liste : les mois sont contigus dans l'année, et
    `serie[debut + heure : fin : 24]` donne directement toutes les heures « 14 h » d'un
    mois. Une version qui reconstruisait des listes d'indices rescannait l'année
    96 fois et coûtait à elle seule l'essentiel du temps de la recherche d'options.

    `detail=False` ne calcule que l'annuel : la recherche d'options n'a besoin de rien
    d'autre, et c'est ce qui la fait tenir dans son budget de temps.
    """
    champs = {
        "production": bilan.prod_h, "consommation": bilan.conso_h,
        "direct": bilan.direct_h, "charge": bilan.charge_h, "decharge": bilan.decharge_h,
        "injecte": bilan.injecte_h, "ecrete": bilan.ecrete_h,
        "stocke_virtuel": bilan.stocke_virtuel_h, "restitue_virtuel": bilan.restitue_virtuel_h,
        "achat": bilan.achat_h,
    }
    annuel = {nom: round(sum(serie), 1) for nom, serie in champs.items()}
    if not detail:
        return {"annuel": annuel, "mensuel": [], "journees": {}}

    mensuel = []
    for mois, (debut, fin) in enumerate(BORNES_MOIS, start=1):
        mensuel.append({"mois": mois,
                        **{nom: round(sum(serie[debut:fin]), 1) for nom, serie in champs.items()}})

    journees = {}
    for saison, mois_saison in SAISONS.items():
        nb_jours = sum((BORNES_MOIS[m - 1][1] - BORNES_MOIS[m - 1][0]) for m in mois_saison) / 24
        points = []
        for heure in range(24):
            point = {}
            for nom, serie in champs.items():
                total = 0.0
                for m in mois_saison:
                    debut, fin = BORNES_MOIS[m - 1]
                    total += sum(serie[debut + heure:fin:24])
                point[nom] = round(total / nb_jours, 3)
            points.append(point)
        journees[saison] = points

    return {"annuel": annuel, "mensuel": mensuel, "journees": journees}


def _economie(config: Configuration, annuel: dict, invest: dict, bilan_virtuel: dict | None) -> dict:
    """Facture, économies, trésorerie sur 25 ans, temps de retour, rendement annuel."""
    kva = config.maison.puissance_souscrite_kva
    prix = prix_kwh(kva)
    abo_elec = abonnement_annuel_eur(kva)
    hausse = (config.hausse_prix_pct_an if config.hausse_prix_pct_an is not None
              else settings.simu_hausse_prix_kwh_pct_an) / 100

    conso_totale = annuel["consommation"]
    achat = annuel["achat"]
    injecte = annuel["injecte"]

    abo_virtuel = bilan_virtuel["abonnement_annuel_eur"] if bilan_virtuel else 0.0
    cout_restitution = bilan_virtuel["cout_restitution_annuel_eur"] if bilan_virtuel else 0.0

    # Référence : la même maison sans aucun solaire.
    facture_reference_an = conso_totale * prix + abo_elec
    facture_an = achat * prix + abo_elec + abo_virtuel + cout_restitution
    revente_an = injecte * settings.solar_prix_revente_eur_kwh
    economie_an = facture_reference_an - facture_an + revente_an

    duree = settings.simu_duree_etude_ans
    vieillissement = settings.simu_vieillissement_panneau_pct_an / 100
    total_invest = invest["total_eur"]

    flux = [-float(total_invest)]
    tresorerie, cumul = [], -float(total_invest)
    for annee in range(1, duree + 1):
        facteur_prix = (1 + hausse) ** (annee - 1)
        facteur_prod = (1 - vieillissement) ** (annee - 1)

        eco_energie = (conso_totale - achat) * prix * facteur_prix * facteur_prod
        if annee <= settings.simu_revente_contrat_ans:
            revente = (injecte * settings.solar_prix_revente_eur_kwh
                       * (1 + settings.simu_revente_indexation_pct_an / 100) ** (annee - 1)
                       * facteur_prod)
        else:
            revente = 0.0  # après le contrat : hypothèse prudente, plus aucun revenu de revente

        cout_annuel = abo_virtuel + cout_restitution * facteur_prod
        # Le lithium se remplace une fois dans les 25 ans. L'inertie, non : sa garantie
        # de 40 ans depasse la duree de l'etude, et c'est precisement la qu'elle rattrape
        # son prix d'achat.
        remplacement = 0.0
        if invest["batterie_eur"] and annee == settings.simu_batterie_duree_vie_ans + 1:
            remplacement = invest["batterie_eur"]

        net = eco_energie + revente - cout_annuel - remplacement
        flux.append(net)
        cumul += net
        tresorerie.append({"annee": annee, "flux_eur": round(net), "cumul_eur": round(cumul)})

    retour = _temps_de_retour(tresorerie, total_invest)
    return {
        "facture_mois_eur": round(facture_an / 12, 1),
        "facture_mois_reference_eur": round(facture_reference_an / 12, 1),
        "abonnement_elec_mois_eur": round(abo_elec / 12, 2),
        "abonnement_virtuel_mois_eur": round(abo_virtuel / 12, 2),
        "economie_1re_annee_eur": round(economie_an),
        "gain_net_25_ans_eur": round(cumul),
        "temps_retour_ans": retour,
        "rendement_annuel_pct": _tri(flux),
        "tresorerie": tresorerie,
        "prix_kwh_eur": prix,
        "hausse_prix_pct_an": round(hausse * 100, 1),
    }


def _temps_de_retour(tresorerie: list[dict], invest: float) -> float | None:
    if invest <= 0:
        return 0.0
    precedent = -invest
    for ligne in tresorerie:
        if ligne["cumul_eur"] >= 0:
            gagne = ligne["cumul_eur"] - precedent
            fraction = (-precedent / gagne) if gagne > 0 else 0.0
            return round(ligne["annee"] - 1 + fraction, 1)
        precedent = ligne["cumul_eur"]
    return None


def _tri(flux: list[float]) -> float | None:
    """Taux de rendement interne, par dichotomie — aucune dépendance ajoutée."""
    def van(taux: float) -> float:
        return sum(f / (1 + taux) ** n for n, f in enumerate(flux))

    if van(0.0) <= 0:
        return None
    bas, haut = 0.0, 1.0
    if van(haut) > 0:
        return None
    for _ in range(80):
        milieu = (bas + haut) / 2
        if van(milieu) > 0:
            bas = milieu
        else:
            haut = milieu
    return round((bas + haut) / 2 * 100, 1)


def _alertes(config: Configuration, annuel: dict, bilan_virtuel: dict | None) -> list[dict]:
    alertes: list[dict] = []
    mono = config.maison.raccordement in ("monophase", "inconnu")

    if config.maison.raccordement == "inconnu":
        alertes.append({
            "niveau": "info",
            "texte": "Raccordement inconnu : le calcul suppose du monophasé, plus contraignant. "
                     "Vérifiez sur votre compteur, le résultat peut changer.",
        })
    # L'écrêtage n'alerte QUE s'il pèse vraiment. Mesuré sur une maison de référence :
    # un 9 kWc monophasé n'écrête rien du tout, et un 12 kWc perd 4 € par an. Deux bandeaux
    # rouges pour cela usaient l'attention du lecteur, qui finissait par ne plus lire les
    # alertes qui comptent. En dessous du seuil, l'écran le dit en petit (onglet Panneaux).
    part_ecretee = 100 * annuel["ecrete"] / annuel["production"] if annuel["production"] else 0.0
    if mono and part_ecretee >= settings.simu_ecretage_alerte_pct:
        alertes.append({
            "niveau": "attention",
            "texte": f"En monophasé, l'injection est plafonnée à "
                     f"{settings.simu_injection_max_kva_mono:g} kVA, et votre installation "
                     f"dépasse ce plafond une bonne partie de l'été : "
                     f"{annuel['ecrete']:.0f} kWh par an ne peuvent pas sortir, soit "
                     f"{part_ecretee:.0f} % de votre production. Le passage en triphasé "
                     f"mérite d'être chiffré.",
        })
    # Il y avait ici une seconde alerte, déclenchée dès que la puissance POSÉE dépassait
    # le plafond d'injection. Elle était fausse en pratique : mesurée sur une maison de
    # référence, une installation de 8, 9 ou 10 kWc en monophasé n'écrête pas un seul kWh,
    # et l'alerte se déclenchait quand même. Ce qui compte n'est pas ce qu'on pose, c'est
    # ce qui sort réellement — et c'est l'écrêtage mesuré, juste au-dessus, qui le dit.
    if bilan_virtuel and not bilan_virtuel["grille_complete"]:
        alertes.append({"niveau": "attention", "texte": bilan_virtuel["note"]})
    if bilan_virtuel and bilan_virtuel["fournisseur_impose"]:
        alertes.append({
            "niveau": "info",
            "texte": f"Cette batterie virtuelle impose de souscrire l'électricité chez "
                     f"{bilan_virtuel['fournisseur_impose']}. À mettre en balance avec votre offre actuelle.",
        })
    return alertes


def hypotheses() -> list[dict]:
    """Ce sur quoi le calcul repose — affiché à l'écran, jamais caché dans le code."""
    return [
        {"libelle": "Prix du kWh (TRV Base, 1er août 2026)",
         "valeur": "0,2001 €/kWh jusqu'à 6 kVA · 0,1985 € à partir de 9 kVA", "statut": "vérifié"},
        {"libelle": "Rachat du surplus",
         "valeur": f"{settings.solar_prix_revente_eur_kwh:.3f} €/kWh, indexé "
                   f"+{settings.simu_revente_indexation_pct_an:g} %/an sur "
                   f"{settings.simu_revente_contrat_ans} ans, puis 0", "statut": "vérifié (juin 2026)"},
        {"libelle": "Prime à l'autoconsommation", "valeur": "aucune depuis juin 2026", "statut": "vérifié"},
        {"libelle": "TVA",
         "valeur": f"{settings.simu_tva_reduite_pct:g} % si ≤ {settings.simu_tva_seuil_kwc:g} kWc sans "
                   f"batterie physique, sinon {settings.simu_tva_pleine_pct:g} % sur tout le projet",
         "statut": "vérifié (carport à confirmer)"},
        {"libelle": "Injection en monophasé",
         "valeur": f"{settings.simu_injection_max_kva_mono:g} kVA maximum", "statut": "vérifié"},
        {"libelle": "Hausse du prix du kWh",
         "valeur": f"{settings.simu_hausse_prix_kwh_pct_an:g} %/an par défaut", "statut": "à confirmer"},
        {"libelle": "Vieillissement des panneaux",
         "valeur": f"{settings.simu_vieillissement_panneau_pct_an:g} %/an", "statut": "à calibrer"},
        {"libelle": "Batterie physique",
         "valeur": f"{settings.simu_batterie_cout_par_kwh_eur} €/kWh, "
                   f"-{settings.simu_batterie_perte_capacite_pct_an:g} %/an, "
                   f"{settings.simu_batterie_duree_vie_ans} ans", "statut": "à calibrer"},
        {"libelle": "Coût d'installation",
         "valeur": "grille par palier, ramenée hors taxes avant application de la TVA due",
         "statut": "à recalibrer sur des sources publiques"},
        {"libelle": "Panneau de référence",
         "valeur": f"{settings.simu_panneau_wc} Wc, {settings.simu_panneau_surface_m2:g} m²",
         "statut": "à recalibrer"},
        {"libelle": "Consommation",
         "valeur": "courbe horaire reconstituée par couches (base, chauffage, eau chaude, "
                   "clim, piscine, véhicule)", "statut": "à calibrer"},
    ]


def calculer(config: Configuration, profil: ProfilConso, prod_h: list[float],
             detail: bool = True, eolien_h: list[float] | None = None,
             eau_litres_h: list[float] | None = None,
             eau_kwh_h: list[float] | None = None) -> dict:
    """Le calcul complet pour une configuration. C'est l'unique porte d'entrée du moteur.

    `detail=False` renvoie tout sauf les bilans mensuels et les journées moyennes : c'est
    le mode de la recherche d'options, qui fait des dizaines de passages et n'a besoin que
    des totaux annuels et de l'économie.
    """
    # L'eolienne produit AVANT tout arbitrage : pour la maison, un kWh de vent et un kWh
    # de soleil sont le meme kWh. Ils se distinguent au prix, a la saison et a l'heure —
    # le vent souffle la nuit et en hiver, quand les panneaux ne donnent rien — mais pas
    # dans le bilan horaire, qui ne connait qu'une production et une consommation.
    eolien_annuel = 0.0
    if eolien_h:
        eolien_annuel = sum(eolien_h)
        prod_h = [p + e for p, e in zip(prod_h, eolien_h)]

    conso_h = profil.total_h

    # LA MACHINE A EAU, deux regimes qui ne se modelisent pas au meme endroit.
    #
    # En marche continue, elle est un usage comme un autre : on l'ajoute a la consommation
    # du foyer AVANT tout arbitrage, et la logique d'autoconsommation decide toute seule
    # de ce que le solaire couvre. Aucune regle speciale, aucun coefficient.
    #
    # Sur solaire seul, elle ne peut plus etre dans la consommation : sa marche DEPEND du
    # surplus disponible, heure par heure. Elle est alors traitee dans la boucle horaire,
    # ou elle se sert avant la batterie.
    eau_sur_surplus = bool(config.eau.modele) and config.eau.solaire_uniquement
    if config.eau.modele and eau_kwh_h and not eau_sur_surplus:
        conso_h = [c + e for c, e in zip(conso_h, eau_kwh_h)]

    if config.stockage.pilotage:
        conso_h = _piloter(conso_h, profil.pilotable_h(), prod_h)

    bilan = _simuler_horaire(
        conso_h, prod_h, config,
        eau_potentiel_kwh=eau_kwh_h if eau_sur_surplus else None,
        eau_potentiel_litres=eau_litres_h if eau_sur_surplus else None,
    )
    agregats = _agreger(bilan, detail=detail)
    annuel = agregats["annuel"]

    # Le bilan de la banque vient du passage horaire, il n'est PAS refait ici : le palier
    # retenu dépend de la pointe de crédit, que les totaux annuels ne portent pas. Le
    # recalculer à partir du volume stocké dans l'année était précisément l'erreur qui
    # louait 3 000 kWh de réserve à un foyer qui n'en détenait jamais 300.
    offre_code = config.stockage.batterie_virtuelle
    offre = batterie_virtuelle.offres().get(offre_code) if offre_code else None
    bilan_virtuel = None
    if offre is not None and bilan.virtuel is not None:
        bilan_virtuel = {
            "code": offre.code, "label": offre.label,
            "stocke_kwh": annuel["stocke_virtuel"], "restitue_kwh": annuel["restitue_virtuel"],
            "credit_maxi_kwh": bilan.virtuel["credit_maxi_kwh"],
            "abonnement_annuel_eur": bilan.virtuel["abonnement_annuel_eur"],
            "cout_restitution_annuel_eur": bilan.virtuel["cout_restitution_annuel_eur"],
            "palier_kwh": bilan.virtuel["palier_kwh"],
            "grille_complete": offre.grille_complete,
            "fournisseur_impose": offre.fournisseur_impose,
            "note": offre.note,
            "conseil": offre.conseil,
            "recommandee": offre.recommandee,
        }

    invest = investissement(config)
    eco = _economie(config, annuel, invest, bilan_virtuel)

    conso_totale = annuel["consommation"] or 1.0
    production = annuel["production"] or 1.0
    autoconso_totale = annuel["direct"] + annuel["decharge"] + annuel["restitue_virtuel"]
    valorisee = annuel["direct"] + annuel["charge"] + annuel["stocke_virtuel"]

    return {
        "indicateurs": {
            "autonomie_pct": round(100 * autoconso_totale / conso_totale, 1),
            "autonomie_part_virtuelle_pct": round(100 * annuel["restitue_virtuel"] / conso_totale, 1),
            "production_valorisee_pct": round(100 * valorisee / production, 1),
            "facture_mois_eur": eco["facture_mois_eur"],
            "facture_mois_reference_eur": eco["facture_mois_reference_eur"],
            "economie_1re_annee_eur": eco["economie_1re_annee_eur"],
            "gain_net_25_ans_eur": eco["gain_net_25_ans_eur"],
            "temps_retour_ans": eco["temps_retour_ans"],
            "rendement_annuel_pct": eco["rendement_annuel_pct"],
            "puissance_kwc": round(_kwc_total(config), 2),
            "nb_usages_pilotes": profil.nb_usages_pilotables() if config.stockage.pilotage else 0,
            "conso_estimee": profil.estime,
        },
        "bilan_annuel": annuel,
        "bilan_mensuel": agregats["mensuel"],
        "journees": agregats["journees"],
        "stockage": {
            "batterie_physique": {
                "nb_packs": config.stockage.nb_packs,
                "capacite_kwh": round(config.stockage.nb_packs * settings.simu_batterie_pack_kwh, 1),
                "charge_kwh": annuel["charge"], "restitue_kwh": annuel["decharge"],
            },
            # La charge et la decharge annuelles sont COMMUNES aux deux stockages : le
            # moteur ne distingue pas d'ou vient un kWh rendu. Les separer demanderait
            # de choisir lequel se vide en premier, une regle qu'aucun des deux
            # fabricants ne donne.
            "inertie": {
                "presente": config.stockage.inertie,
                "capacite_kwh": settings.simu_inertie_capacite_kwh if config.stockage.inertie else 0.0,
                "puissance_kw": settings.simu_inertie_puissance_kw if config.stockage.inertie else 0.0,
                "garantie_ans": settings.simu_inertie_garantie_ans,
                "cout_ttc_eur": round(_inertie_ttc()),
            },
            "batterie_virtuelle": bilan_virtuel,
            # En marche continue la machine tourne a plein : litres et kWh sont ceux du
            # potentiel. Sur solaire seul, c'est la boucle horaire qui a decide, et ses
            # totaux sont plus bas — parfois beaucoup.
            "eau": {
                "modele": config.eau.modele,
                "solaire_uniquement": config.eau.solaire_uniquement,
                "litres_an": round(
                    sum(bilan.eau_litres_h) if eau_sur_surplus else sum(eau_litres_h or [])),
                "kwh_an": round(
                    sum(bilan.eau_kwh_h) if eau_sur_surplus else sum(eau_kwh_h or []), 1),
                "litres_potentiels_an": round(sum(eau_litres_h or [])),
            },
            "eolien": {
                "kwc": config.eolien.kwc,
                "production_kwh": round(eolien_annuel, 1),
                "facteur_anemometre": config.eolien.facteur_anemometre,
            },
            "pilotage": {
                "actif": config.stockage.pilotage,
                "nb_usages": profil.nb_usages_pilotables() if config.stockage.pilotage else 0,
            },
        },
        "investissement": invest,
        "economie": eco,
        "consommation": {
            "annuel_kwh": round(profil.annuel_kwh, 1),
            "estimee": profil.estime,
            "detail_kwh": profil.detail_kwh,
            "equipements_ajoutes": list(profil.ajoutees),
        },
        "alertes": _alertes(config, annuel, bilan_virtuel),
        "hypotheses": hypotheses(),
    }
