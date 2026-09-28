import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SimulateurStudy(Base):
    """Étude du simulateur « maison + équipements », enregistrée par un utilisateur connecté.

    `version_moteur` est stockée avec le résultat : les hypothèses évoluent (tarifs, TVA,
    calibrages), et une étude relue dans deux ans doit dire avec quel moteur elle a été
    produite plutôt que de laisser croire qu'elle est toujours d'actualité.
    """

    __tablename__ = "simulateur_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True
    )
    nom: Mapped[str | None] = mapped_column(String(120), nullable=True)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False)  # l'entrée, rejouable telle quelle
    resultat: Mapped[dict] = mapped_column(JSONB, nullable=False)       # indicateurs + bilans + hypothèses
    version_moteur: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
