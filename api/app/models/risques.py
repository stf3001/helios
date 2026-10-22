"""Risques recensés pour une commune (Géorisques), gardés 30 jours au plus — phase 2."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RisquesCommune(Base):
    __tablename__ = "risques_commune"

    code_insee: Mapped[str] = mapped_column(String(5), primary_key=True)
    commune: Mapped[str | None] = mapped_column(String(120))
    risques: Mapped[list] = mapped_column(JSONB, nullable=False)  # liste fermée de `services/georisques.py`
    catnat_30_ans: Mapped[int | None] = mapped_column(Integer)
    radon_classe: Mapped[int | None] = mapped_column(Integer)
    zone_sismique: Mapped[int | None] = mapped_column(Integer)
    ppr: Mapped[bool | None] = mapped_column(Boolean)
    url_rapport: Mapped[str | None] = mapped_column(String(300))
    collecte_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
