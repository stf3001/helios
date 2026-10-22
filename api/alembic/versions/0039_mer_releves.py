"""Mises en relation, lot 4 : relevés mensuels

- `releves` : le relevé CLOS d'un partenaire pour un mois — instantané JSON et PDF, immuables.
  Un mois non clos n'est pas stocké : il se calcule à la demande et s'affiche « provisoire ».
- `releves_clotures` : la clôture d'un MOIS (une ligne par mois), même sans aucune demande ce
  mois-là — sinon un mois vide paraîtrait éternellement provisoire.

Un relevé n'est pas une facture : ni numéro, ni mentions de facture. Réversible.

Revision ID: 0039_mer_releves
Revises: 0038_mer_espace_partenaire
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0039_mer_releves"
down_revision: Union[str, None] = "0038_mer_espace_partenaire"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "releves_clotures",
        sa.Column("mois", sa.String(7), primary_key=True),
        sa.Column("cloture_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("cloture_par", sa.String(255)),
    )
    op.create_table(
        "releves",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=False, index=True),
        sa.Column("mois", sa.String(7), sa.ForeignKey("releves_clotures.mois"), nullable=False),
        sa.Column("statut", sa.String(12), nullable=False, server_default="clos"),
        sa.Column("instantane", JSONB, nullable=False),
        sa.Column("pdf_path", sa.String(255)),
        sa.Column("cloture_le", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("partner_id", "mois", name="uq_releves_partenaire_mois"),
    )


def downgrade() -> None:
    op.drop_table("releves")
    op.drop_table("releves_clotures")
