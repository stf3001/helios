"""Travaux réceptionnés : ce qui ouvre les garanties de chantier (carnet de maison, lot 1).

Sans `date_reception`, aucune garantie n'est calculée : c'est la réception qui fait courir
le parfait achèvement, le bon fonctionnement et la décennale, pas la facture.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

MAX_TRAVAUX_PAR_MAISON = 40
# Les rénovations du carnet d'information du logement (arrêté du 27/12/2022, articles 2 à 6) ;
# `autre` = hors carnet. Lot 11.
CATEGORIES_CIL = ("isolation_toiture", "isolation_murs", "parois_vitrees_portes", "planchers_bas",
                  "chauffage_froid_ecs", "autre")


class Travaux(Base):
    __tablename__ = "travaux"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nature: Mapped[str] = mapped_column(String(120), nullable=False)
    entreprise: Mapped[str | None] = mapped_column(String(120))
    date_reception: Mapped[date | None] = mapped_column(Date)
    montant_ttc: Mapped[float | None] = mapped_column(Float)
    facture_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("house_documents.id", ondelete="SET NULL")
    )
    attestation_assurance_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("house_documents.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)  # la description des travaux, pour le CIL
    categorie_cil: Mapped[str | None] = mapped_column(String(30))  # CATEGORIES_CIL (lot 11)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
