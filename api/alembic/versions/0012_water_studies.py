"""water_studies (potentiel hydrique / eau atmosphérique Hydrolia)

Revision ID: 0012_water_studies
Revises: 0011_energy_study_type
Create Date: 2026-07-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0012_water_studies"
down_revision: Union[str, None] = "0011_energy_study_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "water_studies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id")),
        sa.Column("params", pg.JSONB(), nullable=False),
        sa.Column("result", pg.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_water_studies_house_id", "water_studies", ["house_id"])


def downgrade() -> None:
    op.drop_table("water_studies")
