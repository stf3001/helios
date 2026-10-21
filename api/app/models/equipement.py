"""Le carnet de maison : un appareil précis, daté, avec sa garantie fabricant (lot 1).

La fiche Maison connaît chaque système par un TYPE et une ANNÉE ; l'équipement porte ce
qu'elle ignore — marque, modèle, garantie, installateur — et survit à son remplacement
(`en_service = False`), pour que l'historique de la maison ne se perde pas.

Tout ce qui est ici est DÉCLARÉ par le foyer. L'âge et le statut des garanties sont
calculés à la lecture (`services/garanties.py`), jamais stockés.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Les codes de la fiche (`schemas/house.py`) sont repris là où ils existent, pour que
# la suggestion « depuis la fiche » n'ait rien à traduire. `autre` vaut dans chaque catégorie.
TYPES_PAR_CATEGORIE: dict[str, tuple[str, ...]] = {
    "chauffage": (
        "PAC_air_eau", "PAC_air_air", "chaudiere_gaz", "chaudiere_fioul", "chaudiere_bois", "poele_bois",
        "poele_granules", "insert", "convecteurs", "radiateurs_inertie", "autre",
    ),
    "ecs": ("ballon_elec", "thermodynamique", "gaz", "solaire", "instantane", "autre"),
    "clim": ("split", "multisplit", "gainable", "PAC_air_air", "autre"),
    "ventilation": ("VMC_simple", "VMC_double", "autre"),
    "production_electricite": ("panneaux_pv", "onduleur", "eolienne", "autre"),
    "stockage": ("batterie", "autre"),
    "recharge": ("borne_recharge", "autre"),
    "eau": (
        "adoucisseur", "fosse_septique", "micro_station", "pompe_piscine",
        "generateur_eau_atmospherique", "autre",
    ),
    "autre": ("autre",),
}
CATEGORIES = tuple(TYPES_PAR_CATEGORIE)
UNITES = ("kW", "kWc", "kWh", "L")
# Les champs de la fiche dont un équipement peut naître (bandeau de suggestions).
ORIGINES_FICHE = ("chauffage_principal", "chauffage_appoint", "ecs", "clim", "ventilation")

MAX_EQUIPEMENTS_PAR_MAISON = 60


class Equipement(Base):
    __tablename__ = "equipements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    categorie: Mapped[str] = mapped_column(String(30), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    marque: Mapped[str | None] = mapped_column(String(80))
    modele: Mapped[str | None] = mapped_column(String(120))
    # Affiché au foyer, JAMAIS transmis au chat ni au LLM (lot 5).
    numero_serie: Mapped[str | None] = mapped_column(String(80))
    puissance: Mapped[float | None] = mapped_column(Float)
    unite: Mapped[str | None] = mapped_column(String(5))
    date_pose: Mapped[date | None] = mapped_column(Date)
    annee_pose: Mapped[int | None] = mapped_column(Integer)  # lue seulement si date_pose est vide
    installateur: Mapped[str | None] = mapped_column(String(120))
    garantie_fabricant_fin: Mapped[date | None] = mapped_column(Date)
    contrat_entretien: Mapped[bool | None] = mapped_column(Boolean)
    contrat_prestataire: Mapped[str | None] = mapped_column(String(120))
    travaux_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("travaux.id", ondelete="SET NULL")
    )
    origine_fiche: Mapped[str | None] = mapped_column(String(30))
    en_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    note: Mapped[str | None] = mapped_column(Text)  # jamais transmise au chat
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", onupdate=lambda: datetime.now(timezone.utc)
    )
