"""Mises en relation, lot 5 : le suivi côté foyer

Sur `leads` :
- `contact_foyer` (`oui`|`non`) et `contact_foyer_le` : la réponse du foyer à « L'entreprise vous
  a-t-elle contacté ? », posée 5 jours ouvrés après la transmission sans contact déclaré ;
- `declarations_foyer` (JSONB) : `[{type, le}]` — devis reçu, travaux signés, projet abandonné.
  Statistiques et écarts seulement : jamais le prix ;
- `sans_contact_signale` : le foyer a répondu « non ». Le prix n'est PAS annulé : l'administration
  le voit et décide.

Réversible.

Revision ID: 0040_mer_suivi_foyer
Revises: 0039_mer_releves
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0040_mer_suivi_foyer"
down_revision: Union[str, None] = "0039_mer_releves"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("contact_foyer", sa.String(3)))
    op.add_column("leads", sa.Column("contact_foyer_le", sa.DateTime(timezone=True)))
    op.add_column("leads", sa.Column("declarations_foyer", JSONB))
    op.add_column("leads", sa.Column("sans_contact_signale", sa.Boolean, nullable=False, server_default=sa.false()))


def downgrade() -> None:
    for col in ("sans_contact_signale", "declarations_foyer", "contact_foyer_le", "contact_foyer"):
        op.drop_column("leads", col)
