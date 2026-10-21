"""Carnet de maison, lot 4 : le journal de la maison — ce qui a été fait, quand, par qui.

Une entrée est DÉCLARÉE ; avec un document joint (facture, rapport), elle est JUSTIFIÉE.
Une entrée qui porte un `tache_id` alimente le moteur d'entretien (`derniers_faits`) : c'est
elle qui fait avancer l'échéance suivante. Les coûts ne sont jamais additionnés ici.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

TYPES_ENTREE = ("entretien", "controle", "reparation", "remplacement", "amelioration", "autre")
MAX_ENTREES_PAR_MAISON = 500


class JournalEntree(Base):
    __tablename__ = "journal_maison"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    titre: Mapped[str] = mapped_column(String(120), nullable=False)
    equipement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipements.id", ondelete="SET NULL")
    )
    piece_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pieces.id", ondelete="SET NULL")
    )
    tache_id: Mapped[str | None] = mapped_column(String(60))  # slug de api/data/entretien/taches.json
    intervenant: Mapped[str | None] = mapped_column(String(120))  # « moi » ou un nom libre
    cout_eur: Mapped[float | None] = mapped_column(Float)  # TTC, facultatif
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("house_documents.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
