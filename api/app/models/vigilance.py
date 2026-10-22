"""Épisodes de vigilance météo orange ou rouge, par département (phase 2)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class VigilanceDepartement(Base):
    __tablename__ = "vigilance_departements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    departement: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    phenomene: Mapped[str] = mapped_column(String(20), nullable=False)  # liste fermée de meteofrance_vigilance
    couleur: Mapped[str] = mapped_column(String(6), nullable=False)     # orange | rouge
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collecte_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
