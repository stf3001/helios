"""energy_studies.type (sobry | courtage) — flux courtage énergie

Revision ID: 0011_energy_study_type
Revises: 0010_agents_log
Create Date: 2026-07-19
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0011_energy_study_type"
down_revision: Union[str, None] = "0010_agents_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("energy_studies", sa.Column("type", sa.String(20), server_default="sobry", nullable=False))


def downgrade() -> None:
    op.drop_column("energy_studies", "type")
