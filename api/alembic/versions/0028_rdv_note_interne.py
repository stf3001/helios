"""Rendez-vous : la note interne de l'équipe

Les statuts `honore`, `absent`, `annule` tiennent dans la colonne `statut` existante
(String(20)) : rien à migrer pour eux. L'index unique sur `debut` n'est PAS touché.

Revision ID: 0028_rdv_note_interne
Revises: 0027_journal
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0028_rdv_note_interne"
down_revision: Union[str, None] = "0027_journal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rendez_vous", sa.Column("note_interne", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rendez_vous", "note_interne")
