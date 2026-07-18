import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

DOC_TYPES = ("dpe", "facture", "photo", "devis", "autre")


class HouseDocument(Base):
    """Document rattaché à une fiche Maison (DPE, facture, photo…) — doc 02."""

    __tablename__ = "house_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # nom d'origine (affichage)
    path: Mapped[str] = mapped_column(String(255), nullable=False)      # chemin de stockage sur le serveur
    size: Mapped[int | None] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
