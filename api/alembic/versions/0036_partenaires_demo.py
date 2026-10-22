"""Partenaires de démonstration (point 60)

`partners.demo` : un partenaire de démonstration (« Démo … », charte datée) n'est visible que des
comptes listés dans `mer_comptes_demo` — jamais dans l'annuaire public, ni dans le chat, ni pour un
autre foyer. Il sert à vérifier les lots de mises en relation sans dater la charte d'un partenaire
réel. Réversible.

Revision ID: 0036_partenaires_demo
Revises: 0035_mer_prix_fixe
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0036_partenaires_demo"
down_revision: Union[str, None] = "0035_mer_prix_fixe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("demo", sa.Boolean, nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("partners", "demo")
