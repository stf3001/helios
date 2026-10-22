"""Carnet, lot 8 : chauffage collectif, et la liste « Avant d'acheter »

- `chauffage_collectif` : oui | non | ne_sais_pas, NOT NULL, `ne_sais_pas` par défaut (fiches
  existantes comprises). Demandé aux appartements seulement ; `oui` → l'entretien de la
  chaudière est assuré par la copropriété. HORS SCORE DE COMPLÉTUDE, comme `zone_old` (0026).
- `avant_achat` : les documents demandés au vendeur par un acheteur (`statut = en_achat`),
  {id_document: {"coche": bool, "document_id": uuid | null}}. Vidé, et archivé au journal,
  quand la fiche passe à `proprietaire`.

Revision ID: 0031_statuts
Revises: 0030_fiche_depuis_carnet
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0031_statuts"
down_revision: Union[str, None] = "0030_fiche_depuis_carnet"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("houses", sa.Column(
        "chauffage_collectif", sa.String(12), nullable=False, server_default=sa.text("'ne_sais_pas'")))
    op.add_column("houses", sa.Column("avant_achat", JSONB))


def downgrade() -> None:
    op.drop_column("houses", "avant_achat")
    op.drop_column("houses", "chauffage_collectif")
