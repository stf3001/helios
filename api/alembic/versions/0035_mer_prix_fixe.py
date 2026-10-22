"""Mises en relation, lot 1 : prix fixe et lien d'intérêt

- `leads.prix_ht` : figé à la création (copie de `mer_prix_ht_eur`) ; `commission` et
  `montant_travaux` restent pour l'historique, plus aucune commission n'est calculée sur un
  lead `travaux` ;
- `partners.lien_interet` : affiché au foyer à côté du nom ;
- données (idempotentes) : AD Solar passe `suspendu` — décision de Stéphane du 22/10/2026,
  « pas partenaire », jamais supprimé — et Hydrolia et Eolia portent leur lien d'intérêt.

Le downgrade retire les deux colonnes ; il ne réactive pas AD Solar (une décision, pas un schéma).

Revision ID: 0035_mer_prix_fixe
Revises: 0034_cil
Create Date: 2026-10-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0035_mer_prix_fixe"
down_revision: Union[str, None] = "0034_cil"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LIEN_FONDATEUR = "Société créée par le fondateur d'Hélios"


def upgrade() -> None:
    op.add_column("leads", sa.Column("prix_ht", sa.Numeric(10, 2)))
    op.add_column("partners", sa.Column("lien_interet", sa.String(200)))
    op.execute("UPDATE partners SET statut = 'suspendu' WHERE raison_sociale = 'AD Solar'")
    op.execute(sa.text("UPDATE partners SET lien_interet = :lien WHERE raison_sociale IN ('Hydrolia', 'Eolia')")
               .bindparams(lien=LIEN_FONDATEUR))


def downgrade() -> None:
    op.drop_column("partners", "lien_interet")
    op.drop_column("leads", "prix_ht")
