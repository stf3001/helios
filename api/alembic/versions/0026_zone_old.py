"""Fiche Maison : le terrain est-il soumis à l'obligation légale de débroussaillement ?

Carnet de maison, lot 3 bis (décision 3 de `briefs/KB-entretien-table.md`) : posée aux
maisons partout en France, jamais aux appartements ; `ne_sais_pas` par défaut, y compris
pour les fiches existantes. HORS SCORE DE COMPLÉTUDE, comme 0021 et 0023.

Revision ID: 0026_zone_old
Revises: 0025_pieces_emetteurs
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026_zone_old"
down_revision: Union[str, None] = "0025_pieces_emetteurs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("houses", sa.Column(
        "zone_old", sa.String(12), nullable=False, server_default=sa.text("'ne_sais_pas'")))


def downgrade() -> None:
    op.drop_column("houses", "zone_old")
