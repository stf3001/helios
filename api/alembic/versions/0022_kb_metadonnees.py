"""Metadonnees documentaires sur kb_documents : empreinte, dates separees, validite, fiabilite, zone

CE N'EST PAS QUE DE LA PREPARATION POUR LE CRAWLER : ca repare une fonction morte.

`crawl_source` ecrivait `date_maj = today` a CHAQUE passage, que le contenu ait change ou
non. Et `run_veille` cherche les documents dont `date_maj` depasse 180 jours. Chaque crawl
remettait donc le compteur a zero sur toute la source : la veille ne pouvait STRUCTURELLEMENT
rien detecter. Le « 0 document perime » consigne comme un test reussi etait la seule reponse
qu'elle savait donner, et les fiches taguees `verif:date_sensible_*` ne seraient jamais
remontees.

Les cinq colonnes, et a quoi chacune sert :

- `empreinte` : SHA-256 du contenu. C'est la piece maitresse. Sans elle, un crawl re-embedde
  les 355 chunks meme quand rien n'a bouge — or l'embedding est la seule operation couteuse
  de l'ingestion (Ollama, en local, sur processeur). A 5 000 documents ce serait des heures
  de calcul pour un resultat identique. Avec elle, on ne recalcule que ce qui a change.

- `date_crawl` : la date du dernier PASSAGE du crawler. C'est ce que `date_maj` contenait en
  realite, sous un nom qui disait autre chose — l'ecran d'administration annoncait « maj »
  en affichant la date du dernier crawl. `date_maj` reprend ici son sens : la date ou le
  CONTENU a change. Verifie avant d'y toucher : seuls le crawler l'ecrit, la veille la lit,
  et `admin_supervision` l'affiche — l'affichage devient juste par la meme occasion.

- `valide_jusqu_au` : la fin de validite quand elle est connue. Les fiches d'aides et de
  reglementation portent deja un tag `verif:date_sensible_<date>` dans le markdown, mais
  c'est du texte libre que RIEN ne sait lire. La veille pourra desormais signaler une fiche
  dont la validite est depassee, ce qu'elle ne sait pas faire du tout aujourd'hui.

- `fiabilite` : la nature de la source. Elle existait deja en partie, dans
  `kb_chunks.metadata.niveau_confiance`, mais codee en dur par TYPE de fichier : « officiel »
  pour tout markdown, « veille » pour tout le web. C'etait faux — les cas pratiques sont des
  profils fictifs, la fiche VOSS une hypothese de lancement, et les deux etaient annoncees
  « officiel ». Elle est maintenant declaree par source, dans `SourceSpec`.
  NOT NULL avec defaut `maison` : les lignes existantes prennent la valeur neutre sans
  retraitement, et le crawler ecrit la vraie au premier passage.

- `zone` : la zone geographique d'application, pour les aides locales que le crawler
  ramenera forcement. Nulle = national, qui est le cas de toute la base aujourd'hui.

CE QUE CETTE MIGRATION NE FAIT PAS, DELIBEREMENT : changer le classement de la recherche.
Faire primer le recent et l'officiel sur un meilleur score vectoriel change ce qu'Helios
REPOND — ca se verifie sur de vraies questions, ca ne se decrete pas dans une migration.
Les donnees d'abord, le classement ensuite, et mesure.

Aucun index : la table compte quelques centaines de lignes, et PostgreSQL les parcourt en
moins de 10 ms (meme raison qu'en 0020, ou l'index approximatif a ete retire).

Revision ID: 0022_kb_metadonnees
Revises: 0021_contrat_electricite
Create Date: 2026-10-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_kb_metadonnees"
down_revision: Union[str, None] = "0021_contrat_electricite"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kb_documents", sa.Column("empreinte", sa.String(64), nullable=True))
    op.add_column("kb_documents", sa.Column("date_crawl", sa.Date(), nullable=True))
    op.add_column("kb_documents", sa.Column("valide_jusqu_au", sa.Date(), nullable=True))
    op.add_column(
        "kb_documents",
        sa.Column("fiabilite", sa.String(20), nullable=False, server_default="maison"),
    )
    op.add_column("kb_documents", sa.Column("zone", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("kb_documents", "zone")
    op.drop_column("kb_documents", "fiabilite")
    op.drop_column("kb_documents", "valide_jusqu_au")
    op.drop_column("kb_documents", "date_crawl")
    op.drop_column("kb_documents", "empreinte")
