"""pro_profiles (espace professionnel)

Revision ID: 0013_pro_profiles
Revises: 0012_water_studies
Create Date: 2026-07-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0013_pro_profiles"
down_revision: Union[str, None] = "0012_water_studies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pro_profiles",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("raison_sociale", sa.String(150)),
        sa.Column("secteur", sa.String(20)),
        sa.Column("code_postal", sa.String(5)),
        sa.Column("surface_m2", sa.Integer()),
        sa.Column("effectif", sa.Integer()),
        sa.Column("equipements", pg.ARRAY(sa.String())),
        sa.Column("conso_annuelle_kwh", sa.Integer()),
        sa.Column("puissance_kva", sa.Integer()),
        sa.Column("fournisseur_actuel", sa.String(80)),
        sa.Column("contrat_actuel", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("pro_profiles")
