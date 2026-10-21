import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TypeEntree = Literal["entretien", "controle", "reparation", "remplacement", "amelioration", "autre"]


class _Commun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intervenant: str | None = Field(default=None, max_length=120)  # « moi » ou un nom
    cout_eur: float | None = Field(default=None, ge=0, le=1_000_000)
    document_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)

    # Un champ s'appelle `date` : le module est importé sous `dt` pour ne pas masquer le type.
    @field_validator("date", check_fields=False)
    @classmethod
    def _pas_dans_le_futur(cls, d: dt.date | None) -> dt.date | None:
        if d is not None and d > dt.date.today():
            raise ValueError("La date ne peut pas être dans le futur : le journal garde ce qui a été fait.")
        return d


class _ChampsEntree(_Commun):
    equipement_id: uuid.UUID | None = None
    piece_id: uuid.UUID | None = None
    tache_id: str | None = Field(default=None, max_length=60)


class EntreeCreate(_ChampsEntree):
    date: dt.date
    type: TypeEntree
    titre: str = Field(min_length=1, max_length=120)


class EntreeUpdate(_ChampsEntree):
    date: dt.date | None = None
    type: TypeEntree | None = None
    titre: str | None = Field(default=None, min_length=1, max_length=120)


class Fait(_Commun):
    """« C'est fait » sur une tâche d'entretien : l'entrée de journal qui la référence."""

    equipement_id: uuid.UUID | None = None  # absent pour une tâche de maison
    date: dt.date = Field(default_factory=dt.date.today)
