"""Batterie virtuelle — moteur générique, paramétré par offre.

Une batterie virtuelle n'est pas un équipement : c'est un contrat. Le surplus n'est pas
vendu, il est « mis de côté » chez un fournisseur, puis restitué plus tard moyennant un
abonnement et parfois un coût par kWh restitué.

Le moteur est générique pour que l'ajout d'une offre soit une ligne de données, pas du
code. Les montants sont dans `config.py`.

CONTRAINTE RÉELLE, jamais masquée : ces offres imposent de changer de fournisseur
d'électricité. Beaucoup de foyers refusent — c'est un critère de choix, pas un détail.

LES DEUX OFFRES MYLIGHT NE DIFFÈRENT PAS PAR LE PRIX, MAIS PAR LA STRUCTURE — et c'est
ce qui décide laquelle conseiller :

- « Stockage sur-mesure » : on loue un VOLUME annuel. L'abonnement dépend du palier choisi,
  il est tout compris, et le transport de l'énergie restituée n'est pas facturé en plus.
- « Stockage illimité » : rien à installer, volume non plafonné, abonnement proportionnel à
  la puissance posée — mais chaque kWh restitué paie son TRANSPORT (acheminement, accise,
  CEE), soit environ 0,11 € en 2026. Sur un foyer qui restitue quelques milliers de kWh
  par an, cette ligne dépasse largement l'écart d'abonnement.

D'où la doctrine de Stéphane, constatée sur ses dossiers réels et inscrite ici dans les
données plutôt que laissée à l'ordre d'un dictionnaire : LE SUR-MESURE DANS 99 % DES CAS.
Le stockage illimité ne devient intéressant que lorsqu'on stocke sur une très longue durée
sans consommer entre-temps — en pratique, la résidence secondaire, qui stocke l'été pour
l'hiver et dont le volume ferait exploser les paliers du sur-mesure.
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class Offre:
    code: str
    label: str
    fournisseur_impose: str | None
    activation_eur: float
    #: Matériel à poser chez le client (coffret MyLight). Zéro pour une offre purement
    #: contractuelle. Entre dans l'investissement, pas dans le coût annuel.
    materiel_eur: float = 0.0
    abonnement_par_kwc_mois: float = 0.0        # mode « proportionnel à la puissance installée »
    #: Mode « palier » : (kWh de RÉSERVE, €/mois). Le kWh est une capacité détenue à un
    #: instant donné — la taille de la batterie virtuelle louée — et NON un volume cumulé
    #: sur l'année. On peut y faire passer 3 000 kWh dans l'année sans jamais en détenir
    #: plus de 300 : c'est le palier 300 qu'on paie. Confirmé par Stéphane le 28/09/2026.
    paliers_kwh: tuple[tuple[int, float], ...] = ()
    cout_restitution_eur_kwh: float = 0.0
    plafond_credit_kwh: float | None = None     # None = pas de plafond
    credit_perdu_fin_annee: bool = True
    grille_complete: bool = True
    note: str = ""
    #: Ce qu'on conseille, et pour qui — distinct de `note`, qui décrit l'offre. L'écran
    #: les affiche différemment : un fait n'a pas le même poids qu'une recommandation.
    conseil: str = ""
    #: Celle qu'on propose quand l'utilisateur n'a rien choisi. Une seule doit l'être.
    recommandee: bool = False

    def palier_pour(self, credit_maxi_kwh: float) -> tuple[int, float] | None:
        """Plus petit palier couvrant la RÉSERVE à détenir (None si l'offre n'a pas de paliers).

        L'argument est le crédit maximal atteint dans l'année, pas le volume stocké sur
        l'année. Confondre les deux revient à louer 3 000 kWh à un foyer qui n'en détient
        jamais plus de 300 — et à conclure que l'offre est trois fois trop chère.
        """
        if not self.paliers_kwh:
            return None
        for kwh, eur in sorted(self.paliers_kwh):
            if kwh >= credit_maxi_kwh:
                return kwh, eur
        return sorted(self.paliers_kwh)[-1]

    def palier_impose(self, palier_force: int | None) -> tuple[int, float] | None:
        """Le palier choisi à la main, s'il existe dans la grille."""
        if palier_force is None:
            return None
        return next((p for p in sorted(self.paliers_kwh) if p[0] == palier_force), None)

    # Pas de méthode « abonnement annuel » sur l'offre : elle a existé, elle prenait un
    # volume en argument, et c'est par elle que le moteur facturait la réserve au prix du
    # volume annuel. L'abonnement se lit maintenant sur le palier RETENU par `simuler()`,
    # qui est le seul endroit à savoir quelle réserve le foyer détient vraiment.


def offres() -> dict[str, Offre]:
    """Catalogue des offres. Construit à la demande pour suivre la config (et les tests)."""
    return {
        # L'ordre compte pour l'affichage : on montre d'abord celle qu'on conseille.
        "mysmartbattery": Offre(
            code="mysmartbattery",
            label="MyLight — Stockage sur-mesure",
            fournisseur_impose="mylight150",
            activation_eur=settings.mylight_activation_eur,
            materiel_eur=settings.simu_msb_materiel_eur,
            paliers_kwh=settings.simu_msb_paliers,
            # Zéro, et ce n'est plus une hypothèse : la grille officielle du 28/09/2026 ne
            # facture aucun coût par kWh restitué sur cette offre. L'abonnement du palier
            # est tout compris.
            cout_restitution_eur_kwh=0.0,
            plafond_credit_kwh=None,
            credit_perdu_fin_annee=True,
            grille_complete=settings.simu_msb_grille_complete,
            recommandee=True,
            note="On loue une réserve, comme une batterie : de 12,99 €/mois pour 20 kWh à "
                 "214,99 €/mois pour 10 000 kWh. On la remplit et on la vide autant de fois "
                 "qu'on veut dans l'année, et l'énergie restituée ne paie pas son transport. "
                 "Demande la pose d'un coffret MyLight.",
            conseil="C'est l'offre à retenir dans la quasi-totalité des cas : sur un foyer qui "
                    "restitue quelques milliers de kWh par an, ne pas payer le transport pèse "
                    "bien plus lourd que l'écart d'abonnement.",
        ),
        "mybattery": Offre(
            code="mybattery",
            label="MyLight — Stockage illimité",
            fournisseur_impose="mylight150",
            activation_eur=settings.mylight_activation_eur,
            abonnement_par_kwc_mois=settings.mylight_abonnement_eur_par_kwc_mois,
            cout_restitution_eur_kwh=settings.mylight_restitution_eur_kwh,
            plafond_credit_kwh=None,
            credit_perdu_fin_annee=True,
            grille_complete=True,
            note="Aucun matériel à poser et aucun plafond de réserve, mais chaque kWh "
                 "restitué paie son transport — acheminement, accise et certificats "
                 "d'économie d'énergie, soit 0,10862 € en 2026 — en plus de l'abonnement de "
                 "1,20 €/kWc par mois.",
            conseil="À réserver aux cas où l'on stocke très longtemps sans rien consommer "
                    "entre-temps : typiquement une résidence secondaire, qui met de côté l'été "
                    "pour l'hiver et dont le volume ferait exploser les paliers du sur-mesure.",
        ),
    }


def _passage(
    besoin_h: list[float], surplus_h: list[float], plafond: float | None,
) -> dict:
    """Un passage dans la banque, sous un plafond de crédit donné (None = aucun).

    Renvoie aussi le CRÉDIT MAXIMAL atteint : c'est lui qui dit quelle réserve il faut
    louer, et il se mesure une fois le surplus de l'heure encaissé, avant la restitution.
    """
    credit = 0.0
    credit_maxi = 0.0
    achat_h: list[float] = []
    stocke_total = 0.0
    restitue_total = 0.0
    refuse_total = 0.0  # surplus que le plafond de crédit n'a pas pu absorber

    for besoin, surplus in zip(besoin_h, surplus_h):
        accepte = surplus
        if plafond is not None:
            place = max(plafond - credit, 0.0)
            accepte = min(surplus, place)
            refuse_total += surplus - accepte
        credit += accepte
        stocke_total += accepte
        if credit > credit_maxi:
            credit_maxi = credit

        restitue = min(besoin, credit)
        credit -= restitue
        restitue_total += restitue
        achat_h.append(besoin - restitue)

    return {
        "achat_h": achat_h,
        "stocke_kwh": stocke_total,
        "restitue_kwh": restitue_total,
        "refuse_kwh": refuse_total,
        "credit_maxi_kwh": credit_maxi,
        "credit_fin_kwh": credit,
    }


def simuler(
    offre: Offre,
    besoin_h: list[float],
    surplus_h: list[float],
    *,
    kwc: float,
    palier_force: int | None = None,
    prix_achat_kwh: float,
    prix_revente_kwh: float,
) -> dict:
    """Passe le surplus dans la banque virtuelle et restitue ce qu'elle peut.

    `besoin_h` = ce qui reste à acheter au réseau avant intervention de la batterie
    virtuelle ; `surplus_h` = ce qui serait injecté sinon. Renvoie l'achat résiduel.

    LE PALIER SE CHOISIT AU MOINS-DISANT, PAS À LA POINTE. C'est le cœur de cette
    fonction, et l'erreur qu'elle a longtemps commise. Louer la réserve qui couvre la
    pointe de crédit garantit de ne rien refuser — mais la pointe est atteinte en fin
    d'été, une fois par an, après des mois d'accumulation. La payer toute l'année coûte
    bien plus cher que ce qu'elle rapporte : ce qui déborde d'une petite réserve n'est
    pas perdu, il part à l'injection et se vend.

    On évalue donc les paliers et on garde celui qui rapporte le plus :

        gain = restitué × prix d'achat évité
             + refusé × prix de revente
             − abonnement − transport de la restitution

    Inutile de monter au-dessus du palier qui couvre la pointe : au-delà, l'énergie ne
    bouge plus d'un kWh et seul l'abonnement grimpe. C'est ce qui borne la recherche, et
    ce qui fait qu'elle coûte quelques passages, pas dix.
    """
    plafond_offre = offre.plafond_credit_kwh
    libre = _passage(besoin_h, surplus_h, plafond_offre)

    def gain(passage: dict, eur_mois: float) -> float:
        return (passage["restitue_kwh"] * prix_achat_kwh
                + passage["refuse_kwh"] * prix_revente_kwh
                - eur_mois * 12
                - passage["restitue_kwh"] * offre.cout_restitution_eur_kwh)

    palier: tuple[int, float] | None = None
    resultat = libre
    if offre.paliers_kwh:
        impose = offre.palier_impose(palier_force)
        if impose is not None:
            palier = impose
            plafond = float(palier[0]) if plafond_offre is None else min(float(palier[0]), plafond_offre)
            resultat = _passage(besoin_h, surplus_h, plafond) if plafond < libre["credit_maxi_kwh"] else libre
        else:
            couvrant = offre.palier_pour(libre["credit_maxi_kwh"])
            plafond_maxi = couvrant[0] if couvrant else 0
            meilleur: float | None = None
            for kwh, eur_mois in sorted(offre.paliers_kwh):
                if kwh > plafond_maxi:
                    break
                plafond = float(kwh) if plafond_offre is None else min(float(kwh), plafond_offre)
                essai = _passage(besoin_h, surplus_h, plafond) if plafond < libre["credit_maxi_kwh"] else libre
                valeur = gain(essai, eur_mois)
                if meilleur is None or valeur > meilleur:
                    meilleur, palier, resultat = valeur, (kwh, eur_mois), essai

    solde = resultat["credit_fin_kwh"] if not offre.credit_perdu_fin_annee else 0.0
    perdu = resultat["credit_fin_kwh"] if offre.credit_perdu_fin_annee else 0.0

    return {
        "achat_h": resultat["achat_h"],
        "stocke_kwh": resultat["stocke_kwh"],
        "restitue_kwh": resultat["restitue_kwh"],
        "refuse_kwh": resultat["refuse_kwh"],
        "credit_maxi_kwh": round(resultat["credit_maxi_kwh"], 1),
        "solde_reporte_kwh": solde,
        "credit_perdu_kwh": perdu,
        "abonnement_annuel_eur": (round(palier[1] * 12, 2) if palier
                                  else round(kwc * offre.abonnement_par_kwc_mois * 12, 2)),
        "cout_restitution_annuel_eur": round(
            resultat["restitue_kwh"] * offre.cout_restitution_eur_kwh, 2),
        "activation_eur": offre.activation_eur,
        "materiel_eur": offre.materiel_eur,
        "palier_kwh": palier[0] if palier else None,
        "grille_complete": offre.grille_complete,
        "fournisseur_impose": offre.fournisseur_impose,
        "note": offre.note,
        "conseil": offre.conseil,
        "recommandee": offre.recommandee,
    }
