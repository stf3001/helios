import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class House(Base):
    """Fiche Maison — un logement par utilisateur en v1 (doc 02)."""

    __tablename__ = "houses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # Bloc Identité du logement (20%) — code_postal requis, reste optionnel
    code_postal: Mapped[str] = mapped_column(String(5), nullable=False)
    type_logement: Mapped[str | None] = mapped_column(String(20))  # maison | appartement
    statut: Mapped[str | None] = mapped_column(String(20))  # proprietaire | locataire | en_achat
    annee_construction: Mapped[str | None] = mapped_column(String(20))  # tranche, ex. "1989-2000"
    surface_habitable: Mapped[int | None] = mapped_column(Integer)
    nb_niveaux: Mapped[int | None] = mapped_column(Integer)
    nb_occupants: Mapped[int | None] = mapped_column(Integer)
    residence_principale: Mapped[bool | None] = mapped_column(Boolean)

    # Bloc Enveloppe (25%)
    isolation_combles: Mapped[str | None] = mapped_column(String(20))  # aucune|partielle|bonne|inconnue
    isolation_combles_annee: Mapped[int | None] = mapped_column(Integer)
    isolation_murs: Mapped[str | None] = mapped_column(String(20))
    isolation_murs_annee: Mapped[int | None] = mapped_column(Integer)
    isolation_plancher: Mapped[str | None] = mapped_column(String(20))
    isolation_plancher_annee: Mapped[int | None] = mapped_column(Integer)
    menuiseries: Mapped[str | None] = mapped_column(String(20))  # simple|double|double_recent|triple
    menuiseries_annee: Mapped[int | None] = mapped_column(Integer)
    ventilation: Mapped[str | None] = mapped_column(String(20))  # aucune|naturelle|VMC_simple|VMC_double|inconnue
    dpe_lettre: Mapped[str | None] = mapped_column(String(1))  # A-G
    dpe_annee: Mapped[int | None] = mapped_column(Integer)

    # Bloc Systèmes (25%)
    chauffage_principal: Mapped[str | None] = mapped_column(String(20))
    chauffage_principal_annee: Mapped[int | None] = mapped_column(Integer)
    chauffage_appoint: Mapped[str | None] = mapped_column(String(20))
    chauffage_appoint_annee: Mapped[int | None] = mapped_column(Integer)
    ecs: Mapped[str | None] = mapped_column(String(20))  # ballon_elec|thermodynamique|gaz|solaire|instantane
    ecs_annee: Mapped[int | None] = mapped_column(Integer)
    clim: Mapped[bool | None] = mapped_column(Boolean)
    clim_type: Mapped[str | None] = mapped_column(String(50))
    regulation: Mapped[str | None] = mapped_column(String(20))  # aucune|thermostat|programmable|connecte

    # Bloc Énergie & factures (15%) — pdl : phase 2, hors score tant que non consenti
    conso_elec_kwh_an: Mapped[int | None] = mapped_column(Integer)
    conso_autre_energie_type: Mapped[str | None] = mapped_column(String(50))
    conso_autre_energie_qte: Mapped[int | None] = mapped_column(Integer)
    puissance_souscrite: Mapped[str | None] = mapped_column(String(10))
    option_tarifaire: Mapped[str | None] = mapped_column(String(10))  # base|HPHC|tempo
    pdl: Mapped[str | None] = mapped_column(String(14))

    # Bloc Projet & désidératas (15%)
    objectifs: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    budget_envisage: Mapped[str | None] = mapped_column(String(20))
    horizon: Mapped[str | None] = mapped_column(String(20))
    travaux_deja_faits: Mapped[str | None] = mapped_column(Text)
    contraintes: Mapped[str | None] = mapped_column(Text)

    # Bloc Toiture / potentiel solaire — hors score J2, exploité au simulateur (J5)
    orientation_toiture: Mapped[str | None] = mapped_column(String(20))
    surface_toit_exploitable: Mapped[int | None] = mapped_column(Integer)
    ombrage: Mapped[str | None] = mapped_column(String(20))  # aucun|partiel|important
    pente: Mapped[int | None] = mapped_column(Integer)

    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", onupdate=lambda: datetime.now(timezone.utc)
    )
