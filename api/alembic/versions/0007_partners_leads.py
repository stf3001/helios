"""schema J8 : partners, leads, reviews (apport d'affaires, doc 08)

Revision ID: 0007_partners_leads
Revises: 0006_energy_studies
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0007_partners_leads"
down_revision: Union[str, None] = "0006_energy_studies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partners",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("raison_sociale", sa.String(150), nullable=False),
        sa.Column("siret", sa.String(14)),
        sa.Column("email", sa.String(255)),
        sa.Column("rge", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("zones", pg.ARRAY(sa.String())),
        sa.Column("metiers", pg.ARRAY(sa.String())),
        sa.Column("charte_signee_at", sa.DateTime(timezone=True)),
        sa.Column("statut", sa.String(20), server_default="candidat", nullable=False),
        sa.Column("note_moyenne", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "leads",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("partner_id", pg.UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("audit_id", pg.UUID(as_uuid=True), sa.ForeignKey("audits.id")),
        sa.Column("type", sa.String(20), server_default="travaux", nullable=False),
        sa.Column("metier", sa.String(30)),
        sa.Column("statut", sa.String(20), server_default="nouveau", nullable=False),
        sa.Column("consent_client_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_retire_at", sa.DateTime(timezone=True)),
        sa.Column("montant_travaux", sa.Integer()),
        sa.Column("commission", sa.Numeric(10, 2)),
        sa.Column("motif_perdu", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_leads_house_id", "leads", ["house_id"])
    op.create_index("ix_leads_partner_id", "leads", ["partner_id"])
    op.create_table(
        "reviews",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", pg.UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False, unique=True),
        sa.Column("note", sa.Integer(), nullable=False),
        sa.Column("commentaire", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    # FK différée de energy_studies.partner_id → partners (colonne créée en 0006, doc 09/§J8)
    op.create_foreign_key(
        "fk_energy_studies_partner", "energy_studies", "partners", ["partner_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_energy_studies_partner", "energy_studies", type_="foreignkey")
    op.drop_table("reviews")
    op.drop_table("leads")
    op.drop_table("partners")
