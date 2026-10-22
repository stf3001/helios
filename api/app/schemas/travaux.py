import uuid
from datetime import date

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# `models/travaux.CATEGORIES_CIL` (lot 11) ; `autre` = hors carnet d'information du logement.
CategorieCil = Literal["isolation_toiture", "isolation_murs", "parois_vitrees_portes", "planchers_bas",
                       "chauffage_froid_ecs", "autre"]


class _Champs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entreprise: str | None = Field(default=None, max_length=120)
    date_reception: date | None = None  # sans elle, aucune garantie n'est calculée
    montant_ttc: float | None = Field(default=None, ge=0, le=10_000_000)
    facture_document_id: uuid.UUID | None = None
    attestation_assurance_document_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)
    categorie_cil: CategorieCil | None = None


class TravauxCreate(_Champs):
    nature: str = Field(min_length=1, max_length=120)


class TravauxUpdate(_Champs):
    nature: str | None = Field(default=None, min_length=1, max_length=120)
