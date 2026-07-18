"""schema : house_documents (upload DPE/facture/photo, doc 02)

Revision ID: 0008_house_documents
Revises: 0007_partners_leads
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0008_house_documents"
down_revision: Union[str, None] = "0007_partners_leads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "house_documents",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", pg.UUID(as_uuid=True), sa.ForeignKey("houses.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("size", sa.Integer()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_house_documents_house_id", "house_documents", ["house_id"])


def downgrade() -> None:
    op.drop_table("house_documents")
