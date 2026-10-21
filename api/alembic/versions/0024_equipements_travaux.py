"""Carnet de maison, lot 1 : équipements datés et travaux réceptionnés

Deux tables rattachées à la maison, effacées avec elle. La fiche Maison n'est PAS touchée :
ses champs `*_annee` restent, aucune synchronisation n'est faite dans ce lot.
`travaux` est créée d'abord, `equipements.travaux_id` pointant vers elle.

Revision ID: 0024_equipements_travaux
Revises: 0023_clim_nb_pieces
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0024_equipements_travaux"
down_revision: Union[str, None] = "0023_clim_nb_pieces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "travaux",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("nature", sa.String(120), nullable=False),
        sa.Column("entreprise", sa.String(120)),
        sa.Column("date_reception", sa.Date()),
        sa.Column("montant_ttc", sa.Float()),
        sa.Column("facture_document_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("house_documents.id", ondelete="SET NULL")),
        sa.Column("attestation_assurance_document_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("house_documents.id", ondelete="SET NULL")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_travaux_house_id", "travaux", ["house_id"])

    op.create_table(
        "equipements",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("categorie", sa.String(30), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("marque", sa.String(80)),
        sa.Column("modele", sa.String(120)),
        sa.Column("numero_serie", sa.String(80)),
        sa.Column("puissance", sa.Float()),
        sa.Column("unite", sa.String(5)),
        sa.Column("date_pose", sa.Date()),
        sa.Column("annee_pose", sa.Integer()),
        sa.Column("installateur", sa.String(120)),
        sa.Column("garantie_fabricant_fin", sa.Date()),
        sa.Column("contrat_entretien", sa.Boolean()),
        sa.Column("contrat_prestataire", sa.String(120)),
        sa.Column("travaux_id", pg.UUID(as_uuid=True), sa.ForeignKey("travaux.id", ondelete="SET NULL")),
        sa.Column("origine_fiche", sa.String(30)),
        sa.Column("en_service", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_equipements_house_id", "equipements", ["house_id"])


def downgrade() -> None:
    op.drop_table("equipements")
    op.drop_table("travaux")
