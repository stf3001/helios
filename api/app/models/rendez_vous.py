"""Rendez-vous telephonique avec un conseiller — 30 minutes, reservable sans compte."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RendezVous(Base):
    __tablename__ = "rendez_vous"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    #: Nullable : reserver ne demande pas de compte. Renseigne si le visiteur est connecte.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    nom: Mapped[str] = mapped_column(String(120), nullable=False)
    telephone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    sujet: Mapped[str | None] = mapped_column(Text)
    #: Debut du creneau. UNIQUE en base : c'est ce qui empeche deux reservations.
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duree_min: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="reserve")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
