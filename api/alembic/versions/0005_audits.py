"""schema J6 : audits (pré-audit déterministe, doc 07 §6)

Revision ID: 0005_audits
Revises: 0004_solar_studies
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0005_audits"
down_revision: Union[str, None] = "0004_solar_studies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("json_result", pg.JSONB(), nullable=False),
        sa.Column("pdf_path", sa.String(255)),
        sa.Column("version_helios", sa.String(10)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audits_house_id", "audits", ["house_id"])


def downgrade() -> None:
    op.drop_table("audits")
