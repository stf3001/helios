"""Les projets de la maison (carnet, lot 9) : un fil de l'idée à la réception des travaux.

Aucun chiffre n'est calculé ici. Budget et économie sont RECOPIÉS d'une étude ou d'un
pré-audit (`etude_ref` dit lequel et de quand), ou DÉCLARÉS d'après un devis du foyer ;
chacun porte sa source, son statut (`calcule`, `suppose`, `declare`) et sa date.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Projet(Base):
    __tablename__ = "projets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    modele_id: Mapped[str] = mapped_column(String(60), nullable=False)
    titre: Mapped[str] = mapped_column(String(120), nullable=False)
    etape: Mapped[str] = mapped_column(String(12), nullable=False, default="idee", server_default="idee")
    # {"type": "simulateur" | "audit" | "eau", "id", "date", ...} — l'étude dont viennent les chiffres.
    etude_ref: Mapped[dict | None] = mapped_column(JSONB)
    budget_bas_eur: Mapped[float | None] = mapped_column(Float)
    budget_haut_eur: Mapped[float | None] = mapped_column(Float)
    budget_source: Mapped[str | None] = mapped_column(String(10))  # etude | audit | devis
    budget_statut: Mapped[str | None] = mapped_column(String(10))  # calcule | suppose | declare
    budget_date: Mapped[date | None] = mapped_column(Date)
    economie_annuelle_eur: Mapped[float | None] = mapped_column(Float)
    economie_source: Mapped[str | None] = mapped_column(String(10))
    economie_statut: Mapped[str | None] = mapped_column(String(10))
    economie_date: Mapped[date | None] = mapped_column(Date)
    devis_document_ids: Mapped[list | None] = mapped_column(JSONB)  # documents de type `devis`
    note: Mapped[str | None] = mapped_column(Text)
    travaux_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("travaux.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", onupdate=lambda: datetime.now(timezone.utc)
    )
