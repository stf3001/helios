import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Cycle de vie d'un lead (doc 08 §2)
LEAD_STATUTS = ("nouveau", "transmis", "contacte", "devis", "signe", "perdu")


class Partner(Base):
    """Entreprise partenaire (apport d'affaires) — doc 08."""

    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raison_sociale: Mapped[str] = mapped_column(String(150), nullable=False)
    siret: Mapped[str | None] = mapped_column(String(14))
    email: Mapped[str | None] = mapped_column(String(255))
    rge: Mapped[bool] = mapped_column(Boolean, default=False)
    zones: Mapped[list[str] | None] = mapped_column(ARRAY(String))    # codes postaux / départements couverts
    metiers: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # pv, pac, isolation, menuiseries, vmc...
    charte_signee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="candidat")  # candidat|actif|suspendu
    note_moyenne: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Lead(Base):
    """Mise en relation client ↔ partenaire — doc 08 §2. Immuable après SIGNÉ (traçabilité commission)."""

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False, index=True)
    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audits.id"))
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="travaux")  # travaux|energie (doc 09)
    metier: Mapped[str | None] = mapped_column(String(30))  # pv, pac, isolation... — sert au calcul de commission
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="nouveau")
    consent_client_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # consentement horodaté
    consent_retire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    montant_travaux: Mapped[int | None] = mapped_column(Integer)  # HT, renseigné à DEVIS/SIGNÉ
    commission: Mapped[float | None] = mapped_column(Numeric(10, 2))
    motif_perdu: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Review(Base):
    """Notation post-chantier du partenaire par le client — doc 08 §2/§4."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, unique=True)
    note: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
