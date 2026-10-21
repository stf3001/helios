"""Carnet de maison, lot 2 : pièces, émetteurs, et la photo d'une pièce

`house_documents.piece_id` rattache UNE photo à une pièce ; elle reste dans les papiers
(SET NULL) si la pièce est supprimée. Ni la fiche Maison ni son score ne sont touchés.

Revision ID: 0025_pieces_emetteurs
Revises: 0024_equipements_travaux
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0025_pieces_emetteurs"
down_revision: Union[str, None] = "0024_equipements_travaux"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pieces",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("nom", sa.String(60), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("niveau", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("surface_m2", sa.Float()),
        sa.Column("chauffee", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("orientation", sa.String(2)),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_pieces_house_id", "pieces", ["house_id"])

    op.create_table(
        "emetteurs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("piece_id", pg.UUID(as_uuid=True), sa.ForeignKey("pieces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("nombre", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("puissance_w", sa.Float()),
        sa.Column("robinet_thermostatique", sa.Boolean()),
        sa.Column("programmable", sa.Boolean()),
        sa.Column("equipement_id", pg.UUID(as_uuid=True), sa.ForeignKey("equipements.id", ondelete="SET NULL")),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_emetteurs_piece_id", "emetteurs", ["piece_id"])

    op.add_column("house_documents", sa.Column(
        "piece_id", pg.UUID(as_uuid=True), sa.ForeignKey("pieces.id", ondelete="SET NULL"), nullable=True))


def downgrade() -> None:
    op.drop_column("house_documents", "piece_id")
    op.drop_table("emetteurs")
    op.drop_table("pieces")
