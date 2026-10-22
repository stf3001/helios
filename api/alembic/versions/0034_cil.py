"""Carnet, lot 11 : les rubriques du carnet d'information du logement

- `equipements.mode_evacuation`, `equipements.etiquette_energie` ;
- `travaux.categorie_cil` ;
- table `isolants`, rattachée à un chantier (effacée avec lui et avec la maison) ;
- le type de document `plan` n'a pas de contrainte en base (liste dans `DOC_TYPES`).
Tout est facultatif. Réversible.

Revision ID: 0034_cil
Revises: 0033_charges_maison
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0034_cil"
down_revision: Union[str, None] = "0033_charges_maison"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("equipements", sa.Column("mode_evacuation", sa.String(12)))
    op.add_column("equipements", sa.Column("etiquette_energie", sa.String(10)))
    op.add_column("travaux", sa.Column("categorie_cil", sa.String(30)))
    op.create_table(
        "isolants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("house_id", UUID(as_uuid=True), sa.ForeignKey("houses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("travaux_id", UUID(as_uuid=True), sa.ForeignKey("travaux.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nature", sa.String(80)),
        sa.Column("marque_reference", sa.String(120)),
        sa.Column("resistance_thermique", sa.Float),
        sa.Column("conductivite", sa.Float),
        sa.Column("epaisseur_mm", sa.Float),
        sa.Column("surface_m2", sa.Float),
        sa.Column("interfaces", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_isolants_house_id", "isolants", ["house_id"])
    op.create_index("ix_isolants_travaux_id", "isolants", ["travaux_id"])


def downgrade() -> None:
    op.drop_index("ix_isolants_travaux_id", table_name="isolants")
    op.drop_index("ix_isolants_house_id", table_name="isolants")
    op.drop_table("isolants")
    op.drop_column("travaux", "categorie_cil")
    op.drop_column("equipements", "etiquette_energie")
    op.drop_column("equipements", "mode_evacuation")
