"""revolt_studies (simulateur PV + batterie + tarifs, à conso égale)

Revision ID: 0014_revolt_studies
Revises: 0013_pro_profiles
Create Date: 2026-07-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0014_revolt_studies"
down_revision: Union[str, None] = "0013_pro_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revolt_studies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("params", pg.JSONB(), nullable=False),
        sa.Column("result", pg.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_revolt_studies_house_id", "revolt_studies", ["house_id"])


def downgrade() -> None:
    op.drop_table("revolt_studies")
