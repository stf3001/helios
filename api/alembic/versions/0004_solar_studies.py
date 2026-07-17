"""schema J5 : solar_studies (potentiel solaire, doc 09 §1)

Revision ID: 0004_solar_studies
Revises: 0003_connected_mode
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0004_solar_studies"
down_revision: Union[str, None] = "0003_connected_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "solar_studies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id")),
        sa.Column("params", pg.JSONB(), nullable=False),
        sa.Column("pvgis_result", pg.JSONB(), nullable=False),
        sa.Column("scenarios", pg.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_solar_studies_house_id", "solar_studies", ["house_id"])


def downgrade() -> None:
    op.drop_table("solar_studies")
