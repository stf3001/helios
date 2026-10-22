"""Les charges déclarées de la maison (carnet, lot 10) : une ligne par maison, tout facultatif.

Ce que la fiche ne sait pas et qu'aucun moteur ne calcule : assurance, taxe foncière,
charges de copropriété, eau, autre. DÉCLARÉ par le foyer, en euros par an. Une valeur
vide se lit « Non renseigné », jamais 0.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ChargesMaison(Base):
    __tablename__ = "charges_maison"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    assurance_eur_an: Mapped[float | None] = mapped_column(Float)
    taxe_fonciere_eur_an: Mapped[float | None] = mapped_column(Float)
    charges_copro_eur_an: Mapped[float | None] = mapped_column(Float)
    eau_eur_an: Mapped[float | None] = mapped_column(Float)
    autre_eur_an: Mapped[float | None] = mapped_column(Float)
    autre_libelle: Mapped[str | None] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", onupdate=lambda: datetime.now(timezone.utc)
    )
