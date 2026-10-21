import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.piece import MAX_PIECES_PAR_MAISON

TypePiece = Literal[
    "sejour", "cuisine", "chambre", "salle_de_bain", "wc", "bureau", "entree", "buanderie",
    "garage", "veranda", "combles_amenages", "autre",
]
Orientation = Literal["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
TypeEmetteur = Literal[
    "radiateur_eau", "convecteur", "panneau_rayonnant", "radiateur_inertie", "seche_serviettes",
    "plancher_chauffant_eau", "plancher_chauffant_elec", "unite_interieure_clim", "poele_bois",
    "poele_granules", "cheminee", "autre",
]


class _ChampsPiece(BaseModel):
    model_config = ConfigDict(extra="forbid")

    niveau: int | None = Field(default=None, ge=-3, le=10)
    surface_m2: float | None = Field(default=None, gt=0, le=500)
    chauffee: bool | None = None
    orientation: Orientation | None = None
    ordre: int | None = Field(default=None, ge=0, le=1000)
    note: str | None = Field(default=None, max_length=2000)


class PieceCreate(_ChampsPiece):
    nom: str = Field(min_length=1, max_length=60)
    type: TypePiece


class PieceUpdate(_ChampsPiece):
    nom: str | None = Field(default=None, min_length=1, max_length=60)
    type: TypePiece | None = None


class Demarrage(BaseModel):
    """Les pièces courantes d'un coup, composées par l'écran (« 3 chambres, 1 salle de bain »)."""

    model_config = ConfigDict(extra="forbid")
    pieces: list[PieceCreate] = Field(min_length=1, max_length=MAX_PIECES_PAR_MAISON)


class _ChampsEmetteur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: int | None = Field(default=None, ge=1, le=50)
    puissance_w: float | None = Field(default=None, gt=0, le=50000)
    robinet_thermostatique: bool | None = None
    programmable: bool | None = None
    equipement_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)


class EmetteurCreate(_ChampsEmetteur):
    type: TypeEmetteur


class EmetteurUpdate(_ChampsEmetteur):
    type: TypeEmetteur | None = None
