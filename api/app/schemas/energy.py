from typing import Literal

from pydantic import BaseModel, Field


class StudyRequest(BaseModel):
    pdl: str = Field(min_length=14, max_length=14, pattern=r"^\d{14}$")
    consent: bool  # doit être True — consentement explicite (doc 09 §2)


class StudyDecision(BaseModel):
    decision: Literal["souscrite", "declinee"]


class CourtageRequest(BaseModel):
    consent: bool  # doit être True — consentement explicite (doc 09 §2)
    # Recueil des infos nécessaires à la demande de courtage (le plus complet possible)
    fournisseur_actuel: str | None = Field(default=None, max_length=80)
    offre_actuelle: str | None = Field(default=None, max_length=100)
    conso_annuelle_kwh: int | None = Field(default=None, ge=0, le=100000)
    puissance_kva: int | None = Field(default=None, ge=3, le=36)
    option_tarifaire: Literal["base", "HPHC", "tempo"] | None = None
    # Meme orthographe que la fiche Maison (`schemas/house.py`) : `courtage_client`
    # retombe sur `house.option_tarifaire` quand le champ est vide, les deux valeurs
    # finissent donc dans le meme dictionnaire. Deux casses = deux options differentes.
    montant_facture_annuelle_eur: int | None = Field(default=None, ge=0)
    pdl: str | None = Field(default=None, min_length=14, max_length=14, pattern=r"^\d{14}$")
