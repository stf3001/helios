"""Etudes du nouveau simulateur « maison + equipements »

Table `simulateur_studies` : une etude enregistree par un utilisateur connecte, avec la
version du moteur qui l'a produite. Aucune table existante n'est touchee ni supprimee —
`solar_studies` et `autoconso_studies` restent en place.

Revision ID: 0018_simulateur_studies
Revises: 0017_rename_autoconso
Create Date: 2026-09-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_simulateur_studies"
down_revision: Union[str, None] = "0017_rename_autoconso"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulateur_studies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("nom", sa.String(length=120), nullable=True),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column("resultat", postgresql.JSONB(), nullable=False),
        sa.Column("version_moteur", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_simulateur_studies_house_id", "simulateur_studies", ["house_id"])


def downgrade() -> None:
    op.drop_index("ix_simulateur_studies_house_id", table_name="simulateur_studies")
    op.drop_table("simulateur_studies")
