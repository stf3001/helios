"""Ce qu'on accepte pour reserver un creneau telephonique."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RendezVousIn(BaseModel):
    debut: datetime
    nom: str = Field(min_length=2, max_length=120)
    #: Assez large pour un numero international avec espaces ou points. On ne valide pas
    #: le format au caractere pres : un numero mal saisi se rattrape au premier appel,
    #: un formulaire qui refuse un numero valide se perd pour toujours.
    telephone: str = Field(min_length=6, max_length=30)
    email: EmailStr | None = None
    sujet: str | None = Field(default=None, max_length=2000)


class RendezVousOut(BaseModel):
    id: str
    debut: datetime
    duree_min: int
