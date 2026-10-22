"""Mises en relation, lot 3 : espace partenaire, charte, justificatifs, contestations

- `contestations` : un partenaire conteste une mise en relation dans les 7 jours (motif,
  commentaire, dates des essais d'appel) ; l'administration accepte ou refuse avec un motif.
- `leads.facturable` (vrai par défaut) : seule une contestation ACCEPTÉE le passe à faux ;
  `prix_ht` est gardé. `leads.contacte_le` : date déclarée par le partenaire (statistiques).
- `partner_documents` : Kbis, décennale, RGE, avec dates ; fichiers sous `generated/partner_docs/`.
- `chartes` : texte de la charte partenaire par version ; `partners.charte_version_signee`.
  AUCUNE version n'est insérée ici : le texte se charge par script, après relecture.
- `partner_activations` : lien d'activation à usage unique (jeton haché, expiration).

Réversible.

Revision ID: 0038_mer_espace_partenaire
Revises: 0037_mer_dossier
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0038_mer_espace_partenaire"
down_revision: Union[str, None] = "0037_mer_dossier"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _id():
    return sa.Column("id", UUID(as_uuid=True), primary_key=True)


def _cree():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    op.add_column("leads", sa.Column("facturable", sa.Boolean, nullable=False, server_default=sa.true()))
    op.add_column("leads", sa.Column("contacte_le", sa.Date))
    op.add_column("partners", sa.Column("charte_version_signee", sa.String(20)))

    op.create_table(
        "contestations", _id(),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False,
                  index=True),
        sa.Column("motif", sa.String(30), nullable=False),
        sa.Column("commentaire", sa.Text, nullable=False),
        sa.Column("essais", JSONB),
        sa.Column("statut", sa.String(12), nullable=False, server_default="en_attente"),
        sa.Column("decision_motif", sa.Text),
        sa.Column("decidee_le", sa.DateTime(timezone=True)),
        _cree(),
    )
    op.create_table(
        "partner_documents", _id(),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("type", sa.String(12), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("date_delivrance", sa.Date),
        sa.Column("date_fin", sa.Date),
        sa.Column("statut", sa.String(10), nullable=False, server_default="depose"),
        sa.Column("motif_refus", sa.Text),
        _cree(),
    )
    op.create_table(
        "chartes",
        sa.Column("version", sa.String(20), primary_key=True),
        sa.Column("texte", sa.Text, nullable=False),
        _cree(),
    )
    op.create_table(
        "partner_activations", _id(),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("jeton_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expire_le", sa.DateTime(timezone=True), nullable=False),
        sa.Column("utilise_le", sa.DateTime(timezone=True)),
        _cree(),
    )


def downgrade() -> None:
    op.drop_table("partner_activations")
    op.drop_table("chartes")
    op.drop_table("partner_documents")
    op.drop_table("contestations")
    op.drop_column("partners", "charte_version_signee")
    op.drop_column("leads", "contacte_le")
    op.drop_column("leads", "facturable")
