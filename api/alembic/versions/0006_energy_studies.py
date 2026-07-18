"""schema J7 : energy_studies (achat d'énergie / SOBRY, doc 09 §2)

Revision ID: 0006_energy_studies
Revises: 0005_audits
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0006_energy_studies"
down_revision: Union[str, None] = "0005_audits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "energy_studies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("partner_id", pg.UUID(as_uuid=True)),  # FK vers partners ajoutée en J8
        sa.Column("pdl", sa.String(14)),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="demandee"),
        sa.Column("result", pg.JSONB()),
        sa.Column("helios_opinion", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_energy_studies_house_id", "energy_studies", ["house_id"])


def downgrade() -> None:
    op.drop_table("energy_studies")
