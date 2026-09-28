"""Courbe de consommation horaire (8 760 h) construite par couches — nouveau simulateur.

Remplace le profil générique dans CE simulateur seulement : `enedis_client` n'est pas
touché, il garde son mécanisme de bascule vers la vraie courbe Linky le jour venu.

Fonction PURE et DÉTERMINISTE : même configuration, même courbe à la virgule près.
Aucun tirage aléatoire, volontairement — un bruit rendrait les bilans intestables et
ferait bouger la facture pour des raisons invisibles à l'utilisateur.

Les couches sont conservées séparément (et non sommées tout de suite) parce que le
pilotage a besoin de savoir QUELLE énergie il a le droit de décaler : le ballon, la
filtration et la recharge du véhicule, jamais le four ni l'éclairage.
"""

from dataclasses import dataclass
from datetime import date

from app.core.config import settings
from app.services.simu_types import Maison

HEURES = 8760
ANNEE = 2019  # année non bissextile → exactement 8 760 points, comme `pvgis` et `enedis_client`

# Couches que le pilotage peut décaler vers les heures de surplus solaire.
PILOTABLES = ("eau_chaude", "piscine", "voiture")


def _calendrier() -> list[tuple[int, int, bool]]:
    """(mois 1-12, heure 0-23, week-end) pour chacune des 8 760 heures de l'année."""
    jours = []
    debut = date(ANNEE, 1, 1).toordinal()
    for quantieme in range(365):
        j = date.fromordinal(debut + quantieme)
        jours.append((j.month, j.weekday() >= 5))
    return [(mois, h, we) for mois, we in jours for h in range(24)]


CALENDRIER = _calendrier()


def _normaliser(valeurs: list[float]) -> list[float]:
    total = sum(valeurs)
    return [v / total for v in valeurs] if total else [0.0] * len(valeurs)


# --- Formes journalières (24 valeurs, normalisées à la construction) -------------

# Foyer absent en journée : deux pointes, matin et soir.
_JOUR_ABSENTS = _normaliser([
    20, 16, 14, 13, 13, 16, 30, 55, 60, 30, 22, 22,
    30, 28, 22, 22, 28, 48, 80, 95, 90, 70, 48, 28,
])
# Foyer présent toute la journée : plus plat, avec un vrai creux de nuit seulement.
_JOUR_PRESENTS = _normaliser([
    20, 16, 14, 13, 13, 16, 28, 45, 50, 48, 46, 52,
    58, 50, 44, 44, 48, 58, 78, 88, 82, 64, 44, 26,
])
# Présence partielle : la moyenne des deux, plutôt qu'une troisième courbe réglée à la main.
_JOUR_PARTIELLE = _normaliser([(a + p) / 2 for a, p in zip(_JOUR_ABSENTS, _JOUR_PRESENTS)])

_FORMES_BASE = {
    "absents": _JOUR_ABSENTS,
    "partielle": _JOUR_PARTIELLE,
    "toute_la_journee": _JOUR_PRESENTS,
}
# Le week-end, tout le monde est chez soi : même forme pour tous, et un peu plus de consommation.
_FACTEUR_WEEKEND = 1.10

# Chauffage : abaissement la nuit, pointes au lever et en soirée.
_JOUR_CHAUFFAGE = _normaliser([
    30, 26, 24, 24, 26, 40, 70, 75, 55, 40, 35, 35,
    38, 38, 36, 38, 48, 65, 78, 80, 70, 58, 44, 34,
])
# Ballon électrique : la nuit par défaut (heures creuses), 1 h → 6 h.
_JOUR_BALLON = _normaliser([0] * 1 + [1] * 5 + [0] * 18)
# Eau chaude instantanée : suit les puisages, matin et soir.
_JOUR_ECS_PUISAGE = _normaliser([
    2, 1, 1, 1, 1, 3, 12, 20, 14, 8, 6, 6,
    8, 6, 5, 5, 7, 12, 18, 16, 12, 8, 5, 3,
])
_JOUR_CLIM = {
    "apres_midi": _normaliser([0] * 13 + [1] * 6 + [0] * 5),   # 13 h → 18 h
    "soiree": _normaliser([0] * 18 + [1] * 5 + [0] * 1),       # 18 h → 22 h
    "nuit": _normaliser([1] * 7 + [0] * 15 + [1] * 2),         # 22 h → 6 h
}
# Filtration de piscine : en journée, quand l'eau est la plus chaude, 9 h → 17 h.
_JOUR_PISCINE = _normaliser([0] * 9 + [1] * 9 + [0] * 6)
_JOUR_VE = {
    "soir": _normaliser([0] * 18 + [1] * 5 + [0] * 1),         # 18 h → 22 h
    "nuit": _normaliser([1] * 6 + [0] * 17 + [1] * 1),         # 23 h → 5 h
}

# --- Poids mensuels (somme = 1) --------------------------------------------------

_MOIS_CHAUFFAGE = [0.19, 0.17, 0.12, 0.07, 0.02, 0.0, 0.0, 0.0, 0.01, 0.07, 0.14, 0.21]
_MOIS_CLIM = [0.0, 0.0, 0.0, 0.0, 0.0, 0.15, 0.35, 0.35, 0.15, 0.0, 0.0, 0.0]
_MOIS_PISCINE = [0.0, 0.0, 0.0, 0.0, 0.15, 0.22, 0.25, 0.23, 0.15, 0.0, 0.0, 0.0]
_MOIS_PLAT = [1 / 12] * 12

_JOURS_PAR_MOIS = [sum(1 for mois, h, _ in CALENDRIER if h == 0 and mois == m) for m in range(1, 13)]


def _grille(defaut: float, table: tuple[tuple[str, float], ...], cle: str) -> float:
    """Lit une valeur dans une grille de config (liste de paires), avec repli."""
    for nom, valeur in table:
        if nom == cle:
            return valeur
    return defaut


def _repartir(
    total_kwh: float,
    poids_mois: list[float],
    forme_jour: list[float],
    *,
    forme_weekend: list[float] | None = None,
    facteur_weekend: float = 1.0,
    masque: list[float] | None = None,
) -> list[float]:
    """Étale `total_kwh` sur l'année selon les poids mensuels et la forme journalière.

    Le masque d'occupation (résidence secondaire) est appliqué APRÈS normalisation :
    une maison inoccupée consomme moins, son énergie ne se reporte pas sur les autres mois.
    """
    if total_kwh <= 0:
        return [0.0] * HEURES

    brut = []
    for mois, heure, weekend in CALENDRIER:
        forme = (forme_weekend or forme_jour) if weekend else forme_jour
        jours = _JOURS_PAR_MOIS[mois - 1]
        poids = poids_mois[mois - 1] / jours if jours else 0.0
        brut.append(poids * forme[heure] * (facteur_weekend if weekend else 1.0))

    somme = sum(brut)
    if somme <= 0:
        return [0.0] * HEURES
    serie = [total_kwh * v / somme for v in brut]
    if masque is not None:
        serie = [v * m for v, m in zip(serie, masque)]
    return serie


def _masque_occupation(maison: Maison) -> list[float] | None:
    """Résidence secondaire : hors des mois d'occupation, il ne reste que la veille."""
    if not maison.residence_secondaire:
        return None
    mois_ok = set(maison.mois_occupation)
    veille = settings.simu_conso_veille_pct / 100
    return [1.0 if mois in mois_ok else veille for mois, _, _ in CALENDRIER]


@dataclass
class ProfilConso:
    couches: dict[str, list[float]]     # nom de couche → 8 760 valeurs (kWh)
    total_h: list[float]
    annuel_kwh: float
    detail_kwh: dict[str, float]        # nom de couche → kWh/an
    estime: bool                        # True si aucune consommation connue n'a été fournie
    ajoutees: tuple[str, ...]           # couches qui s'AJOUTENT à la consommation connue

    def pilotable_h(self) -> list[float]:
        """Énergie décalable heure par heure (ballon + filtration + recharge)."""
        total = [0.0] * HEURES
        for nom in PILOTABLES:
            couche = self.couches.get(nom)
            if couche:
                total = [t + c for t, c in zip(total, couche)]
        return total

    def nb_usages_pilotables(self) -> int:
        return sum(1 for nom in PILOTABLES if sum(self.couches.get(nom) or []) > 0)


def construire(maison: Maison) -> ProfilConso:
    """Construit la courbe horaire du foyer, couche par couche."""
    masque = _masque_occupation(maison)
    couches: dict[str, list[float]] = {}
    ajoutees: list[str] = []

    # --- Base : électroménager, éclairage, veilles ---
    base_kwh = (
        settings.simu_conso_base_fixe_kwh_an
        + settings.simu_conso_base_par_occupant_kwh_an * max(maison.nb_occupants, 1)
    )
    couches["base"] = _repartir(
        base_kwh,
        _MOIS_PLAT,
        _FORMES_BASE.get(maison.presence_journee, _JOUR_ABSENTS),
        forme_weekend=_JOUR_PRESENTS,
        facteur_weekend=_FACTEUR_WEEKEND,
        masque=masque,
    )

    # --- Chauffage (seulement s'il est électrique : les autres énergies ne sont pas ici) ---
    kwh_m2 = _grille(0.0, settings.simu_conso_chauffage_kwh_m2_an, maison.chauffage)
    couches["chauffage"] = _repartir(
        kwh_m2 * maison.surface_m2, _MOIS_CHAUFFAGE, _JOUR_CHAUFFAGE, masque=masque,
    )

    # --- Eau chaude ---
    kwh_ecs = _grille(0.0, settings.simu_conso_ecs_kwh_occupant_an, maison.ecs) * max(maison.nb_occupants, 1)
    forme_ecs = _JOUR_ECS_PUISAGE if maison.ecs == "instantane" else _JOUR_BALLON
    couches["eau_chaude"] = _repartir(kwh_ecs, _MOIS_PLAT, forme_ecs, masque=masque)

    # --- Climatisation ---
    clim = maison.clim
    if clim.present:
        kwh_clim = settings.simu_conso_clim_kwh_piece_an * max(clim.nb_pieces, 1)
        couches["clim"] = _repartir(
            kwh_clim, _MOIS_CLIM, _JOUR_CLIM.get(clim.plage, _JOUR_CLIM["apres_midi"]), masque=masque,
        )
        if not clim.deja_installe:
            ajoutees.append("clim")

    # --- Piscine ---
    piscine = maison.piscine
    if piscine.present:
        if piscine.pompe_kw:
            # Puissance de pompe connue : ~8 h de filtration par jour sur la saison.
            jours_saison = sum(_JOURS_PAR_MOIS[m] for m in range(12) if _MOIS_PISCINE[m] > 0)
            kwh_piscine = piscine.pompe_kw * 8 * jours_saison
        else:
            kwh_piscine = settings.simu_conso_piscine_kwh_m3_an * max(piscine.volume_m3, 1)
        couches["piscine"] = _repartir(kwh_piscine, _MOIS_PISCINE, _JOUR_PISCINE, masque=masque)
        if not piscine.deja_installe:
            ajoutees.append("piscine")

    # --- Véhicule électrique ---
    voiture = maison.voiture
    if voiture.present:
        kwh_ve = voiture.km_an * settings.simu_conso_ve_kwh_100km / 100
        couches["voiture"] = _repartir(
            kwh_ve, _MOIS_PLAT, _JOUR_VE.get(voiture.recharge, _JOUR_VE["nuit"]), masque=masque,
        )
        if not voiture.deja_installe:
            ajoutees.append("voiture")

    # --- Recalage sur la consommation connue -------------------------------------
    # Les équipements AJOUTÉS ne sont pas dans la facture : ils ne participent pas au
    # recalage, ils s'additionnent ensuite. Les autres couches, si.
    existantes = [nom for nom in couches if nom not in ajoutees]
    if maison.conso_connue_kwh_an:
        somme_existantes = sum(sum(couches[nom]) for nom in existantes)
        if somme_existantes > 0:
            facteur = maison.conso_connue_kwh_an / somme_existantes
            for nom in existantes:
                couches[nom] = [v * facteur for v in couches[nom]]

    total_h = [0.0] * HEURES
    for couche in couches.values():
        total_h = [t + c for t, c in zip(total_h, couche)]

    return ProfilConso(
        couches=couches,
        total_h=total_h,
        annuel_kwh=sum(total_h),
        detail_kwh={nom: round(sum(valeurs), 1) for nom, valeurs in couches.items()},
        estime=maison.conso_connue_kwh_an is None,
        ajoutees=tuple(ajoutees),
    )
