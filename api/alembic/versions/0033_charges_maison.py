"""Carnet, lot 10 : les charges déclarées de la maison

Une ligne par maison (`house_id` unique), effacée avec elle. Tout est facultatif : une colonne
vide veut dire « Non renseigné ». Réversible.

Revision ID: 0033_charges_maison
Revises: 0032_projets
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0033_charges_maison"
down_revision: Union[str, None] = "0032_projets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "charges_maison",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("assurance_eur_an", sa.Float),
        sa.Column("taxe_fonciere_eur_an", sa.Float),
        sa.Column("charges_copro_eur_an", sa.Float),
        sa.Column("eau_eur_an", sa.Float),
        sa.Column("autre_eur_an", sa.Float),
        sa.Column("autre_libelle", sa.String(80)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("charges_maison")
