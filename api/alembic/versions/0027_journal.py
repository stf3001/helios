"""Carnet de maison, lot 4 : le journal de la maison

Revision ID: 0027_journal
Revises: 0026_zone_old
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0027_journal"
down_revision: Union[str, None] = "0026_zone_old"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "journal_maison",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("titre", sa.String(120), nullable=False),
        sa.Column("equipement_id", pg.UUID(as_uuid=True), sa.ForeignKey("equipements.id", ondelete="SET NULL")),
        sa.Column("piece_id", pg.UUID(as_uuid=True), sa.ForeignKey("pieces.id", ondelete="SET NULL")),
        sa.Column("tache_id", sa.String(60)),
        sa.Column("intervenant", sa.String(120)),
        sa.Column("cout_eur", sa.Float()),
        sa.Column("document_id", pg.UUID(as_uuid=True), sa.ForeignKey("house_documents.id", ondelete="SET NULL")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_journal_maison_house_id", "journal_maison", ["house_id"])


def downgrade() -> None:
    op.drop_table("journal_maison")
