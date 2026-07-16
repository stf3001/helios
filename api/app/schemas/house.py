import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TypeLogement = Literal["maison", "appartement"]
Statut = Literal["proprietaire", "locataire", "en_achat"]
AnneeConstruction = Literal["avant_1948", "1948_1974", "1975_1988", "1989_2000", "2001_2012", "apres_2012"]
NiveauIsolation = Literal["aucune", "partielle", "bonne", "inconnue"]
Menuiseries = Literal["simple", "double", "double_recent", "triple"]
Ventilation = Literal["aucune", "naturelle", "VMC_simple", "VMC_double", "inconnue"]
DpeLettre = Literal["A", "B", "C", "D", "E", "F", "G"]
Chauffage = Literal["elec_direct", "PAC_air_eau", "PAC_air_air", "gaz", "fioul", "bois", "reseau", "autre"]
Ecs = Literal["ballon_elec", "thermodynamique", "gaz", "solaire", "instantane"]
Regulation = Literal["aucune", "thermostat", "programmable", "connecte"]
PuissanceSouscrite = Literal["3", "6", "9", "12", "15", "18", "24", "30", "36"]
OptionTarifaire = Literal["base", "HPHC", "tempo"]
Objectif = Literal[
    "reduire_facture", "confort_hiver", "confort_ete", "autonomie", "ecologie", "valoriser_bien", "vendre_louer"
]
Budget = Literal["<5k", "5-15k", "15-30k", "30k+", "ne_sait_pas"]
Horizon = Literal["<6mois", "6-24mois", "reflexion"]
Ombrage = Literal["aucun", "partiel", "important"]


class HouseCreate(BaseModel):
    code_postal: str = Field(min_length=5, max_length=5, pattern=r"^\d{5}$")


class HouseUpdate(BaseModel):
    """Tous les champs sont optionnels : la fiche se remplit bloc par bloc, au fil de l'eau."""

    code_postal: str | None = Field(default=None, min_length=5, max_length=5, pattern=r"^\d{5}$")
    type_logement: TypeLogement | None = None
    statut: Statut | None = None
    annee_construction: AnneeConstruction | None = None
    surface_habitable: int | None = Field(default=None, gt=0, le=2000)
    nb_niveaux: int | None = Field(default=None, gt=0, le=20)
    nb_occupants: int | None = Field(default=None, ge=0, le=50)
    residence_principale: bool | None = None

    isolation_combles: NiveauIsolation | None = None
    isolation_combles_annee: int | None = None
    isolation_murs: NiveauIsolation | None = None
    isolation_murs_annee: int | None = None
    isolation_plancher: NiveauIsolation | None = None
    isolation_plancher_annee: int | None = None
    menuiseries: Menuiseries | None = None
    menuiseries_annee: int | None = None
    ventilation: Ventilation | None = None
    dpe_lettre: DpeLettre | None = None
    dpe_annee: int | None = None

    chauffage_principal: Chauffage | None = None
    chauffage_principal_annee: int | None = None
    chauffage_appoint: Chauffage | None = None
    chauffage_appoint_annee: int | None = None
    ecs: Ecs | None = None
    ecs_annee: int | None = None
    clim: bool | None = None
    clim_type: str | None = Field(default=None, max_length=50)
    regulation: Regulation | None = None

    conso_elec_kwh_an: int | None = Field(default=None, ge=0)
    conso_autre_energie_type: str | None = Field(default=None, max_length=50)
    conso_autre_energie_qte: int | None = Field(default=None, ge=0)
    puissance_souscrite: PuissanceSouscrite | None = None
    option_tarifaire: OptionTarifaire | None = None

    objectifs: list[Objectif] | None = None
    budget_envisage: Budget | None = None
    horizon: Horizon | None = None
    travaux_deja_faits: str | None = None
    contraintes: str | None = None

    orientation_toiture: str | None = Field(default=None, max_length=20)
    surface_toit_exploitable: int | None = Field(default=None, ge=0)
    ombrage: Ombrage | None = None
    pente: int | None = Field(default=None, ge=0, le=90)


class HouseOut(HouseUpdate):
    id: uuid.UUID
    code_postal: str
    completeness_score: float
    niveau: str
    block_scores: dict[str, float]
    updated_at: datetime

    class Config:
        from_attributes = True
