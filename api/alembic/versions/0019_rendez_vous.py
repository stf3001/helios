"""Rendez-vous telephoniques avec un conseiller humain

Table `rendez_vous` : un creneau de 30 minutes reserve par un visiteur, connecte ou non.

La contrainte d'unicite sur `debut` EST le mecanisme anti-double-reservation. Deux
visiteurs qui cliquent le meme creneau a la meme seconde ne peuvent pas passer tous les
deux : le second recoit une erreur de la base, pas un rendez-vous fantome. Verifier « le
creneau est-il libre ? » puis inserer laisserait une fenetre entre les deux.

Revision ID: 0019_rendez_vous
Revises: 0018_simulateur_studies
Create Date: 2026-09-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_rendez_vous"
down_revision: Union[str, None] = "0018_simulateur_studies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rendez_vous",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Nullable : on peut reserver sans compte. C'est le but — le rendez-vous est une
        # porte d'entree, pas une recompense reservee aux inscrits.
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("nom", sa.String(length=120), nullable=False),
        sa.Column("telephone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("sujet", sa.Text(), nullable=True),
        sa.Column("debut", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duree_min", sa.Integer(), nullable=False, server_default="30"),
        # libre | honore | annule — l'equipe le fait evoluer depuis le back-office.
        sa.Column("statut", sa.String(length=20), nullable=False, server_default="reserve"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_rendez_vous_debut", "rendez_vous", ["debut"], unique=True)
    op.create_index("ix_rendez_vous_user_id", "rendez_vous", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_rendez_vous_user_id", table_name="rendez_vous")
    op.drop_index("ix_rendez_vous_debut", table_name="rendez_vous")
    op.drop_table("rendez_vous")
