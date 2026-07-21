from typing import Literal

from pydantic import BaseModel, Field

TarifMode = Literal["fixe", "soflex", "socap"]


class RevoltSimulateIn(BaseModel):
    power_kwc: float = Field(gt=0, le=36, description="Puissance de l'installation PV simulée (kWc)")
    battery_kwh: float | None = Field(default=None, gt=0, description="Capacité batterie physique (kWh utile)")
    battery_power_kw: float | None = Field(default=None, gt=0, description="Puissance charge/décharge (kW)")
    mylight: bool = False
    tarif_modes: list[TarifMode] = Field(default_factory=lambda: ["fixe"])
