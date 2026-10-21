import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.equipement import TYPES_PAR_CATEGORIE

Categorie = Literal[
    "chauffage", "ecs", "clim", "ventilation", "production_electricite", "stockage", "recharge", "eau", "autre"
]
Unite = Literal["kW", "kWc", "kWh", "L"]
OrigineFiche = Literal["chauffage_principal", "chauffage_appoint", "ecs", "clim", "ventilation"]


def verifier_type(categorie: str | None, type_: str | None) -> None:
    """Le type doit appartenir à la liste fermée de sa catégorie."""
    if categorie and type_ and type_ not in TYPES_PAR_CATEGORIE[categorie]:
        raise ValueError(f"Type « {type_} » inconnu pour la catégorie « {categorie} »")


class _Champs(BaseModel):
    """Champs communs : un champ inconnu est refusé plutôt que silencieusement ignoré."""

    model_config = ConfigDict(extra="forbid")

    marque: str | None = Field(default=None, max_length=80)
    modele: str | None = Field(default=None, max_length=120)
    numero_serie: str | None = Field(default=None, max_length=80)
    puissance: float | None = Field(default=None, gt=0, le=100000)
    unite: Unite | None = None
    date_pose: date | None = None
    annee_pose: int | None = Field(default=None, ge=1900, le=2100)
    installateur: str | None = Field(default=None, max_length=120)
    garantie_fabricant_fin: date | None = None
    contrat_entretien: bool | None = None
    contrat_prestataire: str | None = Field(default=None, max_length=120)
    travaux_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)


class EquipementCreate(_Champs):
    categorie: Categorie
    type: str = Field(max_length=40)
    origine_fiche: OrigineFiche | None = None
    en_service: bool = True

    @model_validator(mode="after")
    def _type_de_la_categorie(self):
        verifier_type(self.categorie, self.type)
        return self


class EquipementUpdate(_Champs):
    """Tout est optionnel ; la cohérence catégorie/type est revérifiée après fusion."""

    categorie: Categorie | None = None
    type: str | None = Field(default=None, max_length=40)
    en_service: bool | None = None
