"""Recherche exacte dans la base de connaissances : l'index ivfflat est retire

CE N'EST PAS UNE OPTIMISATION, C'EST UNE CORRECTION DE BUG.

L'index pose en 0002 est un `ivfflat ... WITH (lists = 100)`. Un index ivfflat range les
vecteurs dans `lists` paquets et n'en visite que `ivfflat.probes` a chaque recherche —
un seul par defaut. Avec 355 chunks repartis en 100 paquets, un paquet contient trois a
quatre fiches : chaque recherche ne voyait donc QUE CES TROIS-LA, et la bonne fiche,
rangee dans un autre paquet, n'etait jamais atteinte.

Constate le 29/09/2026, en testant une question de potager :

  « quelles plantes associer au potager » ne remontait PAS la fiche « Quelles plantes
  associer au potager, et lesquelles separer ? », pourtant presente et correctement
  vectorisee. Et une recherche demandant 4 resultats en renvoyait 1 — signature meme
  d'un paquet ivfflat presque vide.

Le defaut ne touchait pas que le potager : il degradait TOUTE la base depuis 0002, chat
compris. Il passait inapercu parce qu'une reponse approximative reste une reponse
plausible — c'est exactement le genre de panne qui ne se voit pas.

POURQUOI SUPPRIMER PLUTOT QUE REGLER : la documentation pgvector conseille `lists`
proche de `nb_lignes / 1000`, soit 1 seul paquet ici — autrement dit, pas d'index. Sans
index, PostgreSQL parcourt les 355 vecteurs et rend le VRAI plus proche voisin, mesure a
moins de 10 ms. Un index approximatif se justifie a partir de dizaines de milliers de
fiches ; on en est tres loin, et on le saura quand on y sera.

Le jour ou la base grossira : recreer un index HNSW (meilleur rappel qu'ivfflat) plutot
que de revenir a celui-ci, et VERIFIER LE RAPPEL sur des questions reelles avant de le
garder.

Revision ID: 0020_kb_recherche_exacte
Revises: 0019_rendez_vous
Create Date: 2026-09-29
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0020_kb_recherche_exacte"
down_revision: Union[str, None] = "0019_rendez_vous"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding")


def downgrade() -> None:
    op.execute(
        "CREATE INDEX ix_kb_chunks_embedding ON kb_chunks USING ivfflat "
        "(embedding vector_cosine_ops) WITH (lists = 100)"
    )
