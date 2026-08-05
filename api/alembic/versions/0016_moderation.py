"""Signalements de réponses + journal des accès admin

`message_reports` : le foyer signale une réponse fausse ou gênante — mécanisme qui rend la
constitution vérifiable plutôt que seulement affirmée.

`admin_access_log` : contrepartie de l'accès complet aux données personnelles assumé par le
back-office — chaque consultation nominative est tracée.

Revision ID: 0016_moderation
Revises: 0015_admin_space
Create Date: 2026-07-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0016_moderation"
down_revision: Union[str, None] = "0015_admin_space"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_reports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", pg.UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("motif", sa.String(20), nullable=False),
        sa.Column("commentaire", sa.Text()),
        sa.Column("statut", sa.String(20), nullable=False, server_default="nouveau"),
        sa.Column("note_admin", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_message_reports_message_id", "message_reports", ["message_id"])
    op.create_index("ix_message_reports_user_id", "message_reports", ["user_id"])

    op.create_table(
        "admin_access_log",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_email", sa.String(255), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("cible", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_admin_access_log_created_at", "admin_access_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("admin_access_log")
    op.drop_table("message_reports")
