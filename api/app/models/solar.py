import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SolarStudy(Base):
    """Étude de potentiel solaire — doc 09 §1. house_id nullable : le simulateur est
    ouvert au public (résultats partiels sans compte, complets + stockés si connecté)."""

    __tablename__ = "solar_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id"), index=True
    )
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)  # gps, orientation, pente, surface, ombrage
    pvgis_result: Mapped[dict] = mapped_column(JSONB, nullable=False)  # production annuelle/mensuelle par puissance
    scenarios: Mapped[dict] = mapped_column(JSONB, nullable=False)  # autoconso, économies, retour, batterie
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
