"""Rendez-vous : un créneau annulé redevient réservable

L'index unique sur `debut` couvrait tous les statuts : un rendez-vous annulé gardait son
créneau pris en base, alors que la grille le remontrait comme libre (réserver échouait avec
« Ce créneau vient d'être pris »). Décision de Stéphane (21/10/2026) : le débloquer.

Index unique PARTIEL : deux rendez-vous actifs sur le même instant restent impossibles — c'est
toujours lui, et lui seul, qui empêche une double réservation simultanée.

Revision ID: 0029_rdv_creneau_annule_libre
Revises: 0028_rdv_note_interne
Create Date: 2026-10-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029_rdv_creneau_annule_libre"
down_revision: Union[str, None] = "0028_rdv_note_interne"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_rendez_vous_debut", table_name="rendez_vous")
    op.create_index("ix_rendez_vous_debut", "rendez_vous", ["debut"], unique=True,
                    postgresql_where=sa.text("statut <> 'annule'"))


def downgrade() -> None:
    # Échoue si un créneau annulé a été repris entre-temps : c'est le but de la 0029.
    op.drop_index("ix_rendez_vous_debut", table_name="rendez_vous")
    op.create_index("ix_rendez_vous_debut", "rendez_vous", ["debut"], unique=True)
