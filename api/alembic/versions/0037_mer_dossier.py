"""Mises en relation, lot 2 : le dossier transmis et son score

Sur `leads` : `dossier` (instantané JSON de ce que le foyer a coché, daté), `score` et
`score_detail` (calculés, lus par le partenaire, sans effet sur le prix), `creneaux` (quand
appeler), `contact_nom`, `contact_telephone`, `contact_email`, `message`. Les documents choisis
sont copiés dans `generated/lead_docs/<lead_id>/`. Retirer son consentement efface tout cela,
le statut et le prix restent. Réversible.

Revision ID: 0037_mer_dossier
Revises: 0036_partenaires_demo
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0037_mer_dossier"
down_revision: Union[str, None] = "0036_partenaires_demo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLONNES = (
    ("dossier", JSONB), ("score", sa.Integer), ("score_detail", JSONB), ("creneaux", JSONB),
    ("contact_nom", sa.String(120)), ("contact_telephone", sa.String(30)), ("contact_email", sa.String(255)),
    ("message", sa.Text),
)


def upgrade() -> None:
    for nom, type_ in COLONNES:
        op.add_column("leads", sa.Column(nom, type_))


def downgrade() -> None:
    for nom, _ in reversed(COLONNES):
        op.drop_column("leads", nom)
