"""Entrées du simulateur « maison + équipements » — validation stricte.

`extra="forbid"` partout : un champ mal orthographié doit produire une erreur, pas être
ignoré en silence puis manquer dans le calcul. Toutes les bornes sont explicites —
l'entrée est publique et sans compte.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Presence = Literal["absents", "partielle", "toute_la_journee"]
Orientation = Literal["sud", "sud_est", "sud_ouest", "est", "ouest", "est_ouest"]
Ombrage = Literal["aucun", "partiel", "important"]
Raccordement = Literal["monophase", "triphase", "inconnu"]
Chauffage = Literal["elec_direct", "PAC_air_eau", "PAC_air_air", "gaz", "fioul", "bois", "reseau", "autre"]
Ecs = Literal["ballon_elec", "thermodynamique", "gaz", "solaire", "instantane"]
PlageClim = Literal["apres_midi", "soiree", "nuit"]
RechargeVe = Literal["soir", "nuit"]
Saison = Literal["printemps", "ete", "automne", "hiver"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClimIn(Strict):
    present: bool = False
    deja_installe: bool = True
    nb_pieces: int = Field(default=1, ge=1, le=20)
    plage: PlageClim = "apres_midi"


class PiscineIn(Strict):
    present: bool = False
    deja_installe: bool = True
    volume_m3: int = Field(default=40, ge=1, le=300)
    pompe_kw: float | None = Field(default=None, ge=0.1, le=10)


class VoitureIn(Strict):
    present: bool = False
    deja_installe: bool = True
    km_an: int = Field(default=12000, ge=0, le=100000)
    recharge: RechargeVe = "nuit"
    presente_en_journee: bool = False


class MaisonIn(Strict):
    surface_m2: int = Field(default=100, ge=10, le=2000)
    nb_occupants: int = Field(default=3, ge=1, le=20)
    presence_journee: Presence = "absents"
    residence_secondaire: bool = False
    mois_occupation: list[int] = Field(default_factory=lambda: list(range(1, 13)))
    chauffage: Chauffage = "elec_direct"
    ecs: Ecs = "ballon_elec"
    clim: ClimIn = Field(default_factory=ClimIn)
    piscine: PiscineIn = Field(default_factory=PiscineIn)
    voiture: VoitureIn = Field(default_factory=VoitureIn)
    conso_connue_kwh_an: int | None = Field(default=None, ge=100, le=100000)
    puissance_souscrite_kva: int = Field(default=9, ge=3, le=36)
    raccordement: Raccordement = "inconnu"
    besoin_secours: bool = False

    @model_validator(mode="after")
    def _mois_valides(self):
        if not all(1 <= m <= 12 for m in self.mois_occupation):
            raise ValueError("mois_occupation doit contenir des mois entre 1 et 12")
        return self


class PanneauxIn(Strict):
    nb_panneaux: int = Field(default=0, ge=0, le=40)
    orientation: Orientation = "sud"
    inclinaison: int = Field(default=30, ge=0, le=90)
    ombrage: Ombrage = "aucun"
    nb_panneaux_carport: int = Field(default=0, ge=0, le=40)
    surface_toit_m2: int | None = Field(default=None, ge=0, le=2000)


class StockageIn(Strict):
    nb_packs: int = Field(default=0, ge=0, le=6)
    #: Stockage par inertie : un booleen, pas un compteur. On n'en enterre qu'un.
    inertie: bool = False
    batterie_virtuelle: str | None = Field(default=None, max_length=40)
    palier_virtuel_kwh: int | None = Field(default=None, ge=0, le=100000)
    pilotage: bool = False


class SimulateurIn(Strict):
    """La configuration complète. Adresse OU coordonnées : il en faut une des deux."""

    adresse: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    maison: MaisonIn = Field(default_factory=MaisonIn)
    panneaux: PanneauxIn = Field(default_factory=PanneauxIn)
    stockage: StockageIn = Field(default_factory=StockageIn)
    hausse_prix_pct_an: float | None = Field(default=None, ge=0, le=15)

    @model_validator(mode="after")
    def _localisation_fournie(self):
        if self.adresse is None and (self.lat is None or self.lon is None):
            raise ValueError("Fournissez une adresse, ou une latitude et une longitude")
        return self


class EtudeIn(Strict):
    """Enregistrement d'une étude — la configuration suffit, le résultat est recalculé."""

    nom: str | None = Field(default=None, max_length=120)
    configuration: SimulateurIn
