"""Les isolants posés lors d'un chantier (carnet, lot 11) — une rubrique du carnet
d'information du logement (arrêté du 27/12/2022) : nature, marque et référence, résistance
thermique, conductivité, épaisseur, surface, traitement des interfaces. Tout est DÉCLARÉ et
facultatif ; l'indicateur « À compléter » (`services/cil.py`) dit seulement ce qui manque.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

MAX_ISOLANTS_PAR_MAISON = 100


class Isolant(Base):
    __tablename__ = "isolants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    travaux_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("travaux.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nature: Mapped[str | None] = mapped_column(String(80))           # laine de verre, ouate…
    marque_reference: Mapped[str | None] = mapped_column(String(120))
    resistance_thermique: Mapped[float | None] = mapped_column(Float)  # R, m².K/W
    conductivite: Mapped[float | None] = mapped_column(Float)          # λ, W/m.K
    epaisseur_mm: Mapped[float | None] = mapped_column(Float)
    surface_m2: Mapped[float | None] = mapped_column(Float)
    interfaces: Mapped[str | None] = mapped_column(Text)  # traitement des interfaces, en clair
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
