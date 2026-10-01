"""Le contrat d'electricite rejoint la fiche Maison

Le simulateur demande desormais, sous « Votre raccordement » et sous « Energie », quatre
choses que la fiche ne savait pas garder : les heures creuses, le fournisseur actuel,
l'existence d'un tarif bloque et le nombre de mois qu'il lui reste.

POURQUOI ICI ET PAS DANS L'ETUDE — `api/app/schemas/simulateur.py` est en
`extra="forbid"`. Ajouter ces champs a la configuration du simulateur ferait echouer
CHAQUE calcul en 422, et l'ecran se remplirait de tirets sans dire pourquoi (la panne du
29/09/2026). Ils n'ont d'ailleurs rien a y faire : ils ne pesent sur aucun kWh produit.
Ce sont des reponses utiles a une etude de courtage, et le courtage se joue dans l'espace
client, a partir de la fiche.

`option_tarifaire` existait deja (colonne de 0001) et n'est pas touchee.

HORS SCORE DE COMPLETUDE, volontairement : `completeness.py` note l'etat du LOGEMENT pour
le pre-audit. Un fournisseur ne dit rien des deperditions, et le faire entrer dans le
score ferait baisser celui de toutes les fiches existantes du jour au lendemain.

heures_creuses est une liste de 0 a 2 plages : [{"debut": "13:00", "fin": "15:00"}].
Deux heures et non une duree, parce qu'une plage passe souvent minuit (23:01 -> 07:01).

Revision ID: 0021_contrat_electricite
Revises: 0020_kb_recherche_exacte
Create Date: 2026-10-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_contrat_electricite"
down_revision: Union[str, None] = "0020_kb_recherche_exacte"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("houses", sa.Column("heures_creuses", postgresql.JSONB(), nullable=True))
    op.add_column("houses", sa.Column("fournisseur_actuel", sa.String(length=80), nullable=True))
    op.add_column("houses", sa.Column("tarif_bloque", sa.String(length=10), nullable=True))
    op.add_column(
        "houses", sa.Column("tarif_bloque_mois_restants", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("houses", "tarif_bloque_mois_restants")
    op.drop_column("houses", "tarif_bloque")
    op.drop_column("houses", "fournisseur_actuel")
    op.drop_column("houses", "heures_creuses")
