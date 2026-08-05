"""Renomme revolt_studies -> autoconso_studies

Correction de nommage : « REVOLT » est un logiciel de dimensionnement solaire TIERS (payant,
utilisé par des installateurs), qui n'appartient pas à HELIOS. Il avait été cité comme repère
de qualité lors de la conception, et le nom s'était propagé dans le code par erreur.
Le module s'appelle désormais « autoconso » — descriptif de ce qu'il simule réellement
(autoconsommation : PV + stockage + tarifs, à consommation réelle).

Revision ID: 0017_rename_autoconso
Revises: 0016_moderation
Create Date: 2026-07-27
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0017_rename_autoconso"
down_revision: Union[str, None] = "0016_moderation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("revolt_studies", "autoconso_studies")
    # L'index suit la table : renommé pour rester cohérent avec la convention ix_<table>_<col>.
    op.execute("ALTER INDEX IF EXISTS ix_revolt_studies_house_id RENAME TO ix_autoconso_studies_house_id")


def downgrade() -> None:
    op.execute("ALTER INDEX IF EXISTS ix_autoconso_studies_house_id RENAME TO ix_revolt_studies_house_id")
    op.rename_table("autoconso_studies", "revolt_studies")
