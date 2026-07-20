import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WaterStudy(Base):
    """Étude de potentiel hydrique (eau atmosphérique Hydrolia). house_id nullable : ouvert au public."""

    __tablename__ = "water_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id"), index=True)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)   # ville, modèle
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)   # production annuelle/mensuelle
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
