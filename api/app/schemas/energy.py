from typing import Literal

from pydantic import BaseModel, Field


class StudyRequest(BaseModel):
    pdl: str = Field(min_length=14, max_length=14, pattern=r"^\d{14}$")
    consent: bool  # doit être True — consentement explicite (doc 09 §2)


class StudyDecision(BaseModel):
    decision: Literal["souscrite", "declinee"]


class CourtageRequest(BaseModel):
    consent: bool  # doit être True — consentement explicite (doc 09 §2)
    offre_actuelle: str | None = Field(default=None, max_length=100)  # fournisseur/offre actuels (facultatif)
