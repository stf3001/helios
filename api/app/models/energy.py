import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Cycle de vie d'une étude SOBRY (doc 09 §2)
STATUTS = ("demandee", "recue", "presentee", "souscrite", "declinee")


class EnergyStudy(Base):
    """Étude d'achat d'énergie (SOBRY) — doc 09 §2. Jamais créée sans consentement explicite."""

    __tablename__ = "energy_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # FK vers partners en J8
    pdl: Mapped[str | None] = mapped_column(String(14))
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # consentement horodaté
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="demandee")
    result: Mapped[dict | None] = mapped_column(JSONB)          # estimation SOBRY (ou simulée)
    helios_opinion: Mapped[str | None] = mapped_column(Text)    # avis indépendant, rendu AVANT toute incitation
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
