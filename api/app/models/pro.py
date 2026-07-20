import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Secteurs pro pris en charge (conseils adaptés)
SECTEURS = ("boulangerie", "restauration", "commerce", "artisanat", "bureau", "hotellerie", "autre")
# Équipements énergivores fréquents en pro
EQUIPEMENTS = (
    "four", "chambre_froide", "climatisation", "eclairage_intensif",
    "machines", "air_comprime", "informatique", "chauffage_elec", "vitrine_refrigeree",
)


class ProProfile(Base):
    """Profil professionnel — un client pro identifié (doc 09 §2, extension pro).

    Sa présence indique qu'Helios doit adapter ses questions et conseils au contexte pro.
    """

    __tablename__ = "pro_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    raison_sociale: Mapped[str | None] = mapped_column(String(150))
    secteur: Mapped[str | None] = mapped_column(String(20))          # boulangerie | restauration | ...
    code_postal: Mapped[str | None] = mapped_column(String(5))
    surface_m2: Mapped[int | None] = mapped_column(Integer)
    effectif: Mapped[int | None] = mapped_column(Integer)
    equipements: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    conso_annuelle_kwh: Mapped[int | None] = mapped_column(Integer)
    puissance_kva: Mapped[int | None] = mapped_column(Integer)
    fournisseur_actuel: Mapped[str | None] = mapped_column(String(80))
    contrat_actuel: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
