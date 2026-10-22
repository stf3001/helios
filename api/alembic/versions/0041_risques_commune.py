"""Phase 2 : la commune de la maison et ses risques (Géorisques)

- `houses.code_insee` et `houses.commune` : choisis par le foyer parmi les communes de son code
  postal. Hors score de complétude. Hélios ne demande jamais l'adresse précise.
- `risques_commune` : ce que Géorisques recense pour une commune, réduit aux champs gardés —
  risques présents (liste fermée), arrêtés de catastrophe naturelle des 30 dernières années,
  classe de potentiel radon, zone sismique, existence d'un plan de prévention, lien du rapport,
  date de collecte. Rafraîchi au plus tous les 30 jours.

Réversible.

Revision ID: 0041_risques_commune
Revises: 0040_mer_suivi_foyer
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0041_risques_commune"
down_revision: Union[str, None] = "0040_mer_suivi_foyer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("houses", sa.Column("code_insee", sa.String(5)))
    op.add_column("houses", sa.Column("commune", sa.String(120)))
    op.create_table(
        "risques_commune",
        sa.Column("code_insee", sa.String(5), primary_key=True),
        sa.Column("commune", sa.String(120)),
        sa.Column("risques", JSONB, nullable=False),          # codes de la liste fermée, dans l'ordre d'affichage
        sa.Column("catnat_30_ans", sa.Integer),
        sa.Column("radon_classe", sa.Integer),                 # 1 à 3 (Géorisques)
        sa.Column("zone_sismique", sa.Integer),                # 1 à 5
        sa.Column("ppr", sa.Boolean),                          # un plan de prévention des risques existe
        sa.Column("url_rapport", sa.String(300)),
        sa.Column("collecte_le", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("risques_commune")
    op.drop_column("houses", "commune")
    op.drop_column("houses", "code_insee")
