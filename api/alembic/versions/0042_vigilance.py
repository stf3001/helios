"""Phase 2 : la vigilance météo par département (Météo-France)

`vigilance_departements` : les épisodes ORANGE ou ROUGE en cours ou à venir, et ceux terminés
depuis moins de 8 jours (pour « Noter un dégât » après vent violent ou orages). Une collecte pour
toute la France, au plus toutes les heures ; jamais un appel par foyer. Réversible.

Revision ID: 0042_vigilance
Revises: 0041_risques_commune
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0042_vigilance"
down_revision: Union[str, None] = "0041_risques_commune"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vigilance_departements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("departement", sa.String(3), nullable=False, index=True),
        sa.Column("phenomene", sa.String(20), nullable=False),
        sa.Column("couleur", sa.String(6), nullable=False),     # orange | rouge
        sa.Column("debut", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collecte_le", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("vigilance_departements")
