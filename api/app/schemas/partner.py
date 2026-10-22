import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Ce qu'un candidat peut déclarer : les métiers de l'annuaire (`regions.METIERS`) et trois corps
# d'état sans partenaire à ce jour. « pv » est devenu « solaire » le 22/10/2026 : c'est le code de
# l'annuaire, et un candidat en « pv » n'aurait jamais été proposé.
Metier = Literal["solaire", "pac", "isolation", "eau", "eolien", "inertie", "courtage", "menuiseries", "vmc",
                 "regulation"]


class PartnerApply(BaseModel):
    """Candidature partenaire (/devenir-partenaire)."""
    raison_sociale: str = Field(min_length=2, max_length=150)
    siret: str = Field(min_length=14, max_length=14, pattern=r"^\d{14}$")
    email: str = Field(max_length=255)
    rge: bool = False
    zones: list[str] = Field(default_factory=list)     # codes postaux / départements
    metiers: list[Metier] = Field(default_factory=list)


class Creneau(BaseModel):
    jour: Literal["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
    plage: Literal["matin", "midi", "apres_midi", "soir"]


class Contact(BaseModel):
    nom: str = Field(min_length=1, max_length=120)
    telephone: str | None = Field(default=None, max_length=30, pattern=r"^[0-9+ .()-]*$")  # facultatif
    email: EmailStr


class Partage(BaseModel):
    """Ce que le foyer coche (lot 2). Tout est décoché par défaut : rien ne part sans case cochée."""
    fiche: bool = False
    projet_id: uuid.UUID | None = None
    etude: Literal["audit", "simulateur"] | None = None  # le dernier pré-audit ou la dernière étude
    document_ids: list[uuid.UUID] = Field(default_factory=list)


class LeadDossier(BaseModel):
    """Le dossier d'une demande `travaux` : sert à l'aperçu ET à la création, par la même fonction."""
    metier: str | None = Field(default=None, max_length=30)  # vérifié par la route (`propositions.METIERS_TRAVAUX`)
    partage: Partage = Field(default_factory=Partage)
    contact: Contact | None = None
    creneaux: list[Creneau] = Field(default_factory=list)
    message: str | None = Field(default=None, max_length=2000)


class LeadCreate(LeadDossier):
    partner_id: uuid.UUID
    audit_id: uuid.UUID | None = None
    type: Literal["travaux", "energie"] = "travaux"
    consent: bool  # doit être True (consentement spécifique horodaté, doc 08 §6)


class LeadStatusUpdate(BaseModel):
    statut: Literal["transmis", "contacte", "devis", "signe", "perdu"]
    montant_travaux: int | None = Field(default=None, ge=0)
    motif_perdu: str | None = None


class ReviewCreate(BaseModel):
    note: int = Field(ge=1, le=5)
    commentaire: str | None = Field(default=None, max_length=1000)
