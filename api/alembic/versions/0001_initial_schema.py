"""schema initial J2 : users, refresh_tokens, houses

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("prenom", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_verify_token_hash", sa.String(64)),
        sa.Column("email_verify_token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("consent_cgu_at", sa.DateTime(timezone=True)),
        sa.Column("consent_leads_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "houses",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("code_postal", sa.String(5), nullable=False),
        sa.Column("type_logement", sa.String(20)),
        sa.Column("statut", sa.String(20)),
        sa.Column("annee_construction", sa.String(20)),
        sa.Column("surface_habitable", sa.Integer()),
        sa.Column("nb_niveaux", sa.Integer()),
        sa.Column("nb_occupants", sa.Integer()),
        sa.Column("residence_principale", sa.Boolean()),
        sa.Column("isolation_combles", sa.String(20)),
        sa.Column("isolation_combles_annee", sa.Integer()),
        sa.Column("isolation_murs", sa.String(20)),
        sa.Column("isolation_murs_annee", sa.Integer()),
        sa.Column("isolation_plancher", sa.String(20)),
        sa.Column("isolation_plancher_annee", sa.Integer()),
        sa.Column("menuiseries", sa.String(20)),
        sa.Column("menuiseries_annee", sa.Integer()),
        sa.Column("ventilation", sa.String(20)),
        sa.Column("dpe_lettre", sa.String(1)),
        sa.Column("dpe_annee", sa.Integer()),
        sa.Column("chauffage_principal", sa.String(20)),
        sa.Column("chauffage_principal_annee", sa.Integer()),
        sa.Column("chauffage_appoint", sa.String(20)),
        sa.Column("chauffage_appoint_annee", sa.Integer()),
        sa.Column("ecs", sa.String(20)),
        sa.Column("ecs_annee", sa.Integer()),
        sa.Column("clim", sa.Boolean()),
        sa.Column("clim_type", sa.String(50)),
        sa.Column("regulation", sa.String(20)),
        sa.Column("conso_elec_kwh_an", sa.Integer()),
        sa.Column("conso_autre_energie_type", sa.String(50)),
        sa.Column("conso_autre_energie_qte", sa.Integer()),
        sa.Column("puissance_souscrite", sa.String(10)),
        sa.Column("option_tarifaire", sa.String(10)),
        sa.Column("pdl", sa.String(14)),
        sa.Column("objectifs", pg.ARRAY(sa.String())),
        sa.Column("budget_envisage", sa.String(20)),
        sa.Column("horizon", sa.String(20)),
        sa.Column("travaux_deja_faits", sa.Text()),
        sa.Column("contraintes", sa.Text()),
        sa.Column("orientation_toiture", sa.String(20)),
        sa.Column("surface_toit_exploitable", sa.Integer()),
        sa.Column("ombrage", sa.String(20)),
        sa.Column("pente", sa.Integer()),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_houses_user_id", "houses", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_table("houses")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
