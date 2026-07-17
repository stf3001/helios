from typing import Literal

from pydantic import BaseModel, Field

Orientation = Literal["sud", "sud_est", "sud_ouest", "est", "ouest", "nord_est", "nord_ouest", "nord"]
Ombrage = Literal["aucun", "partiel", "important"]


class SolarSimulateIn(BaseModel):
    # Adresse OU coordonnées directes (l'une des deux voies)
    adresse: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    orientation: Orientation | None = None
    pente: int | None = Field(default=None, ge=0, le=90)
    ombrage: Ombrage | None = None
    surface_toit_m2: int | None = Field(default=None, ge=0, le=1000)
    conso_kwh_an: int | None = Field(default=None, ge=0)  # ignoré en mode connecté (on prend la fiche)
