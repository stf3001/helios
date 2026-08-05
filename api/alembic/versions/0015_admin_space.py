"""Espace admin : drapeau is_admin sur users + score RAG sur messages

`users.is_admin` : authentifie le back-office en réutilisant le JWT existant (plus
robuste que le seul secret partagé X-Admin-Token, qui reste dispo pour les scripts).

`messages.rag_score` : meilleur score de similarité trouvé au moment de la réponse.
Instrumentation nécessaire au module « questions sans réponse » (score sous le seuil
= trou dans la base de connaissances). Ajouté ici pour éviter une seconde migration.

Revision ID: 0015_admin_space
Revises: 0014_revolt_studies
Create Date: 2026-07-27
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0015_admin_space"
down_revision: Union[str, None] = "0014_revolt_studies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("messages", sa.Column("rag_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "rag_score")
    op.drop_column("users", "is_admin")
