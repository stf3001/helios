"""schema J4 : citations/coût sur messages (mode connecté + routeur hybride)

Revision ID: 0003_connected_mode
Revises: 0002_kb_chat
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0003_connected_mode"
down_revision: Union[str, None] = "0002_kb_chat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("citations", pg.JSONB()))
    op.add_column("messages", sa.Column("chunks_used", pg.JSONB()))
    op.add_column("messages", sa.Column("constitution_version", sa.String(10)))
    op.add_column("messages", sa.Column("estimated_cost_eur", sa.Float()))


def downgrade() -> None:
    op.drop_column("messages", "estimated_cost_eur")
    op.drop_column("messages", "constitution_version")
    op.drop_column("messages", "chunks_used")
    op.drop_column("messages", "citations")
