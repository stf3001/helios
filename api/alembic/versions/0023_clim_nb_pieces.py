"""Le nombre de pieces climatisees rejoint la fiche Maison

Le pre-audit devait supposer une piece climatisee (« clim oui/non » ne dit pas combien),
ce qui fausse le chauffage deduit de la facture d'une maison tout electrique.
`clim_type` reste en texte libre pour les fiches existantes.

HORS SCORE DE COMPLETUDE, volontairement, comme 0021 : y entrer ce champ ferait baisser
le score de toutes les fiches existantes du jour au lendemain.

Revision ID: 0023_clim_nb_pieces
Revises: 0022_kb_metadonnees
Create Date: 2026-10-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_clim_nb_pieces"
down_revision: Union[str, None] = "0022_kb_metadonnees"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("houses", sa.Column("clim_nb_pieces", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("houses", "clim_nb_pieces")
