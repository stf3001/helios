import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.db import Base


class KbDocument(Base):
    """Un document source (ex. une entrée FAQ) — doc 02, doc 07.

    LES DEUX DATES NE DISENT PAS LA MÊME CHOSE, et c'est tout l'objet de la migration 0022 :
    `date_maj` est la date où le CONTENU a changé, `date_crawl` celle du dernier passage du
    crawler. Tant qu'il n'y en avait qu'une, le crawler la remettait à aujourd'hui à chaque
    passage et la veille ne pouvait plus rien repérer. **Ne jamais écrire `date_maj` sans
    avoir constaté que l'empreinte a bougé.**
    """

    __tablename__ = "kb_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # ex. "faq_maison"
    titre: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    date_maj: Mapped[date] = mapped_column(Date, nullable=False)  # dernier changement de CONTENU
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="actif")  # actif | obsolete

    #: SHA-256 du contenu (migration 0022). Sert à ne ré-embedder que ce qui a réellement
    #: changé : l'embedding est la seule opération coûteuse de l'ingestion. Nulle sur un
    #: document ingéré avant la migration — le prochain crawl la renseigne.
    empreinte: Mapped[str | None] = mapped_column(String(64))
    #: Dernier passage du crawler, qu'il ait trouvé du nouveau ou non.
    date_crawl: Mapped[date | None] = mapped_column(Date)
    #: Fin de validité quand elle est connue (barèmes d'aides, échéances réglementaires).
    #: Dépassée = la veille le signale. Nulle = pas de péremption connue.
    valide_jusqu_au: Mapped[date | None] = mapped_column(Date)
    #: Nature de la source, déclarée dans `agents_engine.SourceSpec` :
    #: officiel | maison | constructeur | hypothese | pedagogique | veille.
    fiabilite: Mapped[str] = mapped_column(String(20), nullable=False, default="maison")
    #: Zone géographique d'application (département, région). Nulle = national.
    zone: Mapped[str | None] = mapped_column(String(50))


class KbChunk(Base):
    """Un chunk vectorisé — 1 Q/R de FAQ = 1 chunk en v1 (doc 07 §2)."""

    __tablename__ = "kb_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kb_documents.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dimensions), nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
