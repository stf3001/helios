import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AgentLog(Base):
    """Journal des agents automatisés (crawler d'ingestion, veille marché) — doc 02 / doc 10."""

    __tablename__ = "agents_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent: Mapped[str] = mapped_column(String(20), nullable=False)   # crawler | veille
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # ex. ingest_source, stale_flag, error
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
