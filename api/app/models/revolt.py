import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RevoltStudy(Base):
    """Simulation « Revolt » (PV + batterie + tarifs) — toujours liée à une fiche maison
    (fonctionnalité réservée aux utilisateurs connectés). Conservée gratuitement dans
    l'espace client, et exploitable par Helios dans le chat (contexte de conversation)."""

    __tablename__ = "revolt_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)   # power_kwc, battery_*, mylight, tarif_modes
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)   # production, consommation, lignes (comparaison)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
