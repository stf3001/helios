from typing import Literal

from pydantic import BaseModel, Field

Secteur = Literal["boulangerie", "restauration", "commerce", "artisanat", "bureau", "hotellerie", "autre"]


class ProProfileIn(BaseModel):
    raison_sociale: str | None = Field(default=None, max_length=150)
    secteur: Secteur | None = None
    code_postal: str | None = Field(default=None, pattern=r"^\d{5}$")
    surface_m2: int | None = Field(default=None, ge=0, le=100000)
    effectif: int | None = Field(default=None, ge=0, le=10000)
    equipements: list[str] = Field(default_factory=list)
    conso_annuelle_kwh: int | None = Field(default=None, ge=0)
    puissance_kva: int | None = Field(default=None, ge=0, le=250)
    fournisseur_actuel: str | None = Field(default=None, max_length=80)
    contrat_actuel: str | None = Field(default=None, max_length=100)


class ProCourtageRequest(BaseModel):
    consent: bool
    montant_facture_annuelle_eur: int | None = Field(default=None, ge=0)
