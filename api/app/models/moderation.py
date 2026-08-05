import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Motifs proposés au client — volontairement peu nombreux et explicites.
MOTIFS = ("faux", "hors_sujet", "genant", "incomprehensible", "autre")
STATUTS = ("nouveau", "traite", "ignore")


class MessageReport(Base):
    """Signalement d'une réponse d'Helios par le foyer.

    C'est le mécanisme qui rend la constitution vérifiable : sans retour terrain, « Helios ne
    dit jamais de bêtise » resterait une affirmation invérifiable. `user_id` est nullable car
    le chat est aussi ouvert aux visiteurs anonymes.
    """

    __tablename__ = "message_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    motif: Mapped[str] = mapped_column(String(20), nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="nouveau")
    note_admin: Mapped[str | None] = mapped_column(Text)  # ce qui a été fait du signalement
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class AdminAccessLog(Base):
    """Trace des consultations de données personnelles par un administrateur.

    L'accès aux conversations et aux fiches foyer est complet (choix assumé) : ce journal en est
    la contrepartie — il rend l'accès traçable, et répond à une demande RGPD éventuelle.
    """

    __tablename__ = "admin_access_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)   # ex. conversation_lue, export_rgpd
    cible: Mapped[str | None] = mapped_column(String(255))            # identifiant ou email concerné
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", index=True)
