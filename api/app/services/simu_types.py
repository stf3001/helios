"""Types partagés du simulateur « maison + équipements » — étape 1.

Des dataclasses plutôt que les schémas Pydantic : les moteurs (`simu_conso`,
`simu_engine`, `simu_options`) restent des fonctions pures, testables sans FastAPI
ni réseau. La conversion depuis la requête HTTP se fait dans le routeur.
"""

from dataclasses import dataclass, field, replace

# Valeurs acceptées — reprises du vocabulaire de la fiche Maison quand il existe.
PRESENCES = ("absents", "partielle", "toute_la_journee")
ORIENTATIONS = ("sud", "sud_est", "sud_ouest", "est", "ouest", "est_ouest")
OMBRAGES = ("aucun", "partiel", "important")
RACCORDEMENTS = ("monophase", "triphase", "inconnu")
PLAGES_CLIM = ("apres_midi", "soiree", "nuit")
RECHARGES_VE = ("soir", "nuit")
SAISONS = ("printemps", "ete", "automne", "hiver")


@dataclass(frozen=True)
class Equipement:
    """Un usage électrique du foyer.

    `deja_installe` est la distinction qui compte : un équipement déjà là est DÉJÀ
    compris dans la consommation annuelle connue — il ne fait que façonner la courbe.
    Un équipement ajouté par la simulation s'additionne à cette consommation.
    """

    present: bool = False
    deja_installe: bool = True


@dataclass(frozen=True)
class Clim(Equipement):
    nb_pieces: int = 1
    plage: str = "apres_midi"


@dataclass(frozen=True)
class Piscine(Equipement):
    volume_m3: int = 40
    pompe_kw: float | None = None


@dataclass(frozen=True)
class Voiture(Equipement):
    km_an: int = 12000
    recharge: str = "nuit"
    presente_en_journee: bool = False


@dataclass(frozen=True)
class Maison:
    """Le foyer et ses usages — ce qui fabrique la courbe de consommation."""

    surface_m2: int = 100
    nb_occupants: int = 3
    presence_journee: str = "absents"
    residence_secondaire: bool = False
    mois_occupation: tuple[int, ...] = tuple(range(1, 13))  # 1 = janvier
    chauffage: str = "elec_direct"
    ecs: str = "ballon_elec"
    clim: Clim = field(default_factory=Clim)
    piscine: Piscine = field(default_factory=Piscine)
    voiture: Voiture = field(default_factory=Voiture)
    conso_connue_kwh_an: int | None = None
    puissance_souscrite_kva: int = 9
    raccordement: str = "inconnu"
    besoin_secours: bool = False


@dataclass(frozen=True)
class Panneaux:
    nb_panneaux: int = 0
    orientation: str = "sud"
    inclinaison: int = 30
    ombrage: str = "aucun"
    nb_panneaux_carport: int = 0
    surface_toit_m2: int | None = None


@dataclass(frozen=True)
class Stockage:
    nb_packs: int = 0
    #: Stockage par inertie : une unite ou rien. Pas un compteur — on n'en enterre pas deux.
    inertie: bool = False
    batterie_virtuelle: str | None = None  # code d'offre, cf. batterie_virtuelle.OFFRES
    palier_virtuel_kwh: int | None = None
    pilotage: bool = False


@dataclass(frozen=True)
class Eolien:
    """Une eolienne Tulipe, ou rien. `kwc` a zero veut dire pas d'eolienne."""

    kwc: float = 0.0
    #: Recalage sur une mesure d'anemometre : EOLIA prete l'appareil un mois, et le
    #: rapport entre le vent mesure et celui de la station donne ce coefficient. Sans
    #: mesure il vaut 1, et l'estimation reste celle de la station la plus proche.
    facteur_anemometre: float = 1.0


@dataclass(frozen=True)
class Lieu:
    lat: float
    lon: float
    commune: str | None = None


@dataclass(frozen=True)
class Configuration:
    """Tout ce qui décrit une simulation. Immuable : les options en dérivent par `replace`."""

    lieu: Lieu
    maison: Maison = field(default_factory=Maison)
    panneaux: Panneaux = field(default_factory=Panneaux)
    eolien: Eolien = field(default_factory=Eolien)
    stockage: Stockage = field(default_factory=Stockage)
    hausse_prix_pct_an: float | None = None  # None = valeur par défaut de la config

    def avec(self, **kw) -> "Configuration":
        """Variante de cette configuration — utilisée par la recherche d'options."""
        return replace(self, **kw)
