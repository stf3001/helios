"""schema J10 : agents_log (agents crawler + veille, doc 02/10)

Revision ID: 0010_agents_log
Revises: 0009_partner_password
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0010_agents_log"
down_revision: Union[str, None] = "0009_partner_password"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents_log",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent", sa.String(20), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agents_log")
