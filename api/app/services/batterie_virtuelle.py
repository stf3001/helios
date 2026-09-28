"""Batterie virtuelle — moteur générique, paramétré par offre.

Une batterie virtuelle n'est pas un équipement : c'est un contrat. Le surplus n'est pas
vendu, il est « mis de côté » chez un fournisseur, puis restitué plus tard moyennant un
abonnement et parfois un coût par kWh restitué.

Le moteur est générique pour que l'ajout d'une offre soit une ligne de données, pas du
code. Les montants sont dans `config.py`.

CONTRAINTE RÉELLE, jamais masquée : ces offres imposent de changer de fournisseur
d'électricité. Beaucoup de foyers refusent — c'est un critère de choix, pas un détail.
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class Offre:
    code: str
    label: str
    fournisseur_impose: str | None
    activation_eur: float
    abonnement_par_kwc_mois: float = 0.0        # mode « proportionnel à la puissance installée »
    paliers_kwh: tuple[tuple[int, float], ...] = ()  # mode « palier » : (kWh/an, €/mois)
    cout_restitution_eur_kwh: float = 0.0
    plafond_credit_kwh: float | None = None     # None = pas de plafond
    credit_perdu_fin_annee: bool = True
    grille_complete: bool = True
    note: str = ""

    def palier_pour(self, kwh_a_stocker: float) -> tuple[int, float] | None:
        """Plus petit palier couvrant le volume à stocker (None si l'offre n'a pas de paliers)."""
        if not self.paliers_kwh:
            return None
        for kwh, eur in sorted(self.paliers_kwh):
            if kwh >= kwh_a_stocker:
                return kwh, eur
        return sorted(self.paliers_kwh)[-1]

    def abonnement_annuel_eur(self, kwc: float, kwh_a_stocker: float, palier_force: int | None = None) -> float:
        if self.paliers_kwh:
            if palier_force is not None:
                choix = next((p for p in sorted(self.paliers_kwh) if p[0] == palier_force), None)
                if choix is None:
                    choix = self.palier_pour(kwh_a_stocker)
            else:
                choix = self.palier_pour(kwh_a_stocker)
            return round(choix[1] * 12, 2) if choix else 0.0
        return round(kwc * self.abonnement_par_kwc_mois * 12, 2)


def offres() -> dict[str, Offre]:
    """Catalogue des offres. Construit à la demande pour suivre la config (et les tests)."""
    return {
        "mybattery": Offre(
            code="mybattery",
            label="MyLight — MyBattery",
            fournisseur_impose="mylight150",
            activation_eur=settings.mylight_activation_eur,
            abonnement_par_kwc_mois=settings.mylight_abonnement_eur_par_kwc_mois,
            cout_restitution_eur_kwh=settings.mylight_restitution_eur_kwh,
            plafond_credit_kwh=None,
            credit_perdu_fin_annee=True,
            grille_complete=True,
            note="Abonnement proportionnel à la puissance installée ; la restitution reste "
                 "facturée (TURPE + accise). Tarifs relevés publiquement, à confirmer auprès "
                 "de MyLight avant toute décision.",
        ),
        "mysmartbattery": Offre(
            code="mysmartbattery",
            label="MyLight — MySmartBattery",
            fournisseur_impose="mylight150",
            activation_eur=settings.simu_msb_activation_eur,
            paliers_kwh=settings.simu_msb_paliers,
            cout_restitution_eur_kwh=0.0,  # abonnement supposé tout compris — À CONFIRMER
            plafond_credit_kwh=None,
            credit_perdu_fin_annee=True,
            grille_complete=settings.simu_msb_grille_complete,
            note="GRILLE INCOMPLÈTE : seuls les deux paliers extrêmes sont sourcés. Les paliers "
                 "intermédiaires restent à relever et à dater auprès de MyLight — d'ici là, le "
                 "chiffrage de cette offre est provisoire et probablement pessimiste.",
        ),
    }


def simuler(
    offre: Offre,
    besoin_h: list[float],
    surplus_h: list[float],
    *,
    kwc: float,
    palier_force: int | None = None,
) -> dict:
    """Passe le surplus dans la banque virtuelle et restitue ce qu'elle peut.

    `besoin_h` = ce qui reste à acheter au réseau avant intervention de la batterie
    virtuelle ; `surplus_h` = ce qui serait injecté sinon. Renvoie l'achat résiduel.
    """
    credit = 0.0
    achat_h: list[float] = []
    stocke_total = 0.0
    restitue_total = 0.0
    refuse_total = 0.0  # surplus que le plafond de crédit n'a pas pu absorber

    for besoin, surplus in zip(besoin_h, surplus_h):
        accepte = surplus
        if offre.plafond_credit_kwh is not None:
            place = max(offre.plafond_credit_kwh - credit, 0.0)
            accepte = min(surplus, place)
            refuse_total += surplus - accepte
        credit += accepte
        stocke_total += accepte

        restitue = min(besoin, credit)
        credit -= restitue
        restitue_total += restitue
        achat_h.append(besoin - restitue)

    solde = credit if not offre.credit_perdu_fin_annee else 0.0
    perdu = credit if offre.credit_perdu_fin_annee else 0.0

    abonnement = offre.abonnement_annuel_eur(kwc, stocke_total, palier_force)
    palier = offre.palier_pour(stocke_total) if offre.paliers_kwh else None

    return {
        "achat_h": achat_h,
        "stocke_kwh": stocke_total,
        "restitue_kwh": restitue_total,
        "refuse_kwh": refuse_total,
        "solde_reporte_kwh": solde,
        "credit_perdu_kwh": perdu,
        "abonnement_annuel_eur": abonnement,
        "cout_restitution_annuel_eur": round(restitue_total * offre.cout_restitution_eur_kwh, 2),
        "activation_eur": offre.activation_eur,
        "palier_kwh": palier[0] if palier else None,
        "grille_complete": offre.grille_complete,
        "fournisseur_impose": offre.fournisseur_impose,
        "note": offre.note,
    }
