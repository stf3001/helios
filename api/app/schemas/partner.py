import uuid
from typing import Literal

from pydantic import BaseModel, Field

Metier = Literal["pv", "pac", "isolation", "menuiseries", "vmc", "regulation"]


class PartnerApply(BaseModel):
    """Candidature partenaire (/devenir-partenaire)."""
    raison_sociale: str = Field(min_length=2, max_length=150)
    siret: str = Field(min_length=14, max_length=14, pattern=r"^\d{14}$")
    email: str = Field(max_length=255)
    rge: bool = False
    zones: list[str] = Field(default_factory=list)     # codes postaux / départements
    metiers: list[Metier] = Field(default_factory=list)


class LeadCreate(BaseModel):
    partner_id: uuid.UUID
    audit_id: uuid.UUID | None = None
    type: Literal["travaux", "energie"] = "travaux"
    metier: Metier | None = None
    consent: bool  # doit être True (consentement spécifique horodaté, doc 08 §6)


class LeadStatusUpdate(BaseModel):
    statut: Literal["transmis", "contacte", "devis", "signe", "perdu"]
    montant_travaux: int | None = Field(default=None, ge=0)
    motif_perdu: str | None = None


class ReviewCreate(BaseModel):
    note: int = Field(ge=1, le=5)
    commentaire: str | None = Field(default=None, max_length=1000)
