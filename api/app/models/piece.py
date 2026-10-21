"""Carnet de maison, lot 2 : la maison pièce par pièce, et ce qui chauffe ou rafraîchit chacune.

Saisie DÉCLARATIVE : rien ici n'alimente encore un calcul. Le pré-audit et le
dimensionnement PAC/clim liront ces tables dans un lot ultérieur (point 36 de TODO.md).
La fiche Maison n'est jamais corrigée à partir des pièces : un écart est seulement signalé
(`services/pieces.py`).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

TYPES_PIECE = (
    "sejour", "cuisine", "chambre", "salle_de_bain", "wc", "bureau", "entree", "buanderie",
    "garage", "veranda", "combles_amenages", "autre",
)
ORIENTATIONS = ("N", "NE", "E", "SE", "S", "SO", "O", "NO")
TYPES_EMETTEUR = (
    "radiateur_eau", "convecteur", "panneau_rayonnant", "radiateur_inertie", "seche_serviettes",
    "plancher_chauffant_eau", "plancher_chauffant_elec", "unite_interieure_clim", "poele_bois",
    "poele_granules", "cheminee", "autre",
)

MAX_PIECES_PAR_MAISON = 25
MAX_EMETTEURS_PAR_PIECE = 10


class Piece(Base):
    __tablename__ = "pieces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("houses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nom: Mapped[str] = mapped_column(String(60), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    niveau: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")  # -1 sous-sol
    surface_m2: Mapped[float | None] = mapped_column(Float)
    chauffee: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    orientation: Mapped[str | None] = mapped_column(String(2))
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Emetteur(Base):
    __tablename__ = "emetteurs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    piece_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pieces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    puissance_w: Mapped[float | None] = mapped_column(Float)  # par unité
    robinet_thermostatique: Mapped[bool | None] = mapped_column(Boolean)  # radiateur_eau seulement
    programmable: Mapped[bool | None] = mapped_column(Boolean)
    # L'équipement du lot 1 qui le produit : chaudière, PAC, multisplit. Facultatif.
    equipement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipements.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
