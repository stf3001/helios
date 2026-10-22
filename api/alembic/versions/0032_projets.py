"""Carnet, lot 9 : les projets de la maison

Une table, `projets`, effacée avec la maison (cascade, comme le reste du carnet). Le chantier
créé à la fin reste si le projet est supprimé (SET NULL). Réversible.

Revision ID: 0032_projets
Revises: 0031_statuts
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0032_projets"
down_revision: Union[str, None] = "0031_statuts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("modele_id", sa.String(60), nullable=False),
        sa.Column("titre", sa.String(120), nullable=False),
        sa.Column("etape", sa.String(12), nullable=False, server_default="idee"),
        sa.Column("etude_ref", JSONB),
        sa.Column("budget_bas_eur", sa.Float),
        sa.Column("budget_haut_eur", sa.Float),
        sa.Column("budget_source", sa.String(10)),
        sa.Column("budget_statut", sa.String(10)),
        sa.Column("budget_date", sa.Date),
        sa.Column("economie_annuelle_eur", sa.Float),
        sa.Column("economie_source", sa.String(10)),
        sa.Column("economie_statut", sa.String(10)),
        sa.Column("economie_date", sa.Date),
        sa.Column("devis_document_ids", JSONB),
        sa.Column("note", sa.Text),
        sa.Column("travaux_id", UUID(as_uuid=True), sa.ForeignKey("travaux.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_projets_house_id", "projets", ["house_id"])


def downgrade() -> None:
    op.drop_index("ix_projets_house_id", table_name="projets")
    op.drop_table("projets")
