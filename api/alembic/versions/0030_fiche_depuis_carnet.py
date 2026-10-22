"""Carnet, lot 7 : la fiche reprend les équipements reliés (point 35)

Migration de DONNÉES, sans changement de schéma. Pour chaque maison dont un équipement en
service porte `origine_fiche` :
1. un équipement sans date face à une fiche datée prend l'année de la fiche (à la reprise
   seulement — décision du 22/10/2026) ;
2. puis l'équipement gagne sur chaque écart restant ;
chaque geste s'écrit au journal de la maison (type `autre`, « Fiche mise à jour depuis le
carnet », ancienne valeur en note), et le score de complétude est recalculé.

Idempotente : relancée, elle ne trouve plus d'écart et n'écrit rien. La règle vient de
`services/fiche_equipements.reprise` — la même table que la synchronisation en direct, pour
que la reprise et l'application ne puissent pas diverger. Le revers est connu : si cette
table change un jour, rejouer 0030 sur une base neuve appliquerait la nouvelle version.

Le downgrade ne fait rien : les anciennes valeurs sont dans le journal, pas en colonne.

Revision ID: 0030_fiche_depuis_carnet
Revises: 0029_rdv_creneau_annule_libre
Create Date: 2026-10-22
"""
import uuid
from datetime import date
from types import SimpleNamespace
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.services import fiche_equipements as fe
from app.services.completeness import compute_score

revision: str = "0030_fiche_depuis_carnet"
down_revision: Union[str, None] = "0029_rdv_creneau_annule_libre"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    lignes = bind.execute(sa.text(
        "SELECT id, house_id, categorie, type, date_pose, annee_pose, origine_fiche, en_service "
        "FROM equipements WHERE en_service AND origine_fiche IS NOT NULL ORDER BY created_at"
    )).mappings().all()
    par_maison: dict = {}
    for ligne in lignes:
        par_maison.setdefault(ligne["house_id"], []).append(SimpleNamespace(**ligne))

    aujourd_hui = date.today()
    for house_id, equipements in par_maison.items():
        maison = SimpleNamespace(**bind.execute(
            sa.text("SELECT * FROM houses WHERE id = :id"), {"id": house_id}).mappings().one())
        r = fe.reprise(maison, equipements, aujourd_hui)
        for eq_id, annee in r["annees"].items():
            bind.execute(sa.text("UPDATE equipements SET annee_pose = :a WHERE id = :id"),
                         {"a": annee, "id": eq_id})
        if r["fiche"]:
            for champ, valeur in r["fiche"].items():
                setattr(maison, champ, valeur)
            sets = ", ".join(f"{c} = :{c}" for c in r["fiche"])
            bind.execute(sa.text(f"UPDATE houses SET {sets}, completeness_score = :score WHERE id = :id"),
                         {**r["fiche"], "score": compute_score(maison), "id": house_id})
        for entree in r["journal"]:
            bind.execute(sa.text(
                "INSERT INTO journal_maison (id, house_id, date, type, titre, equipement_id, note) "
                "VALUES (:id, :house_id, :date, :type, :titre, :equipement_id, :note)"
            ), {**entree, "id": uuid.uuid4(), "house_id": house_id})


def downgrade() -> None:
    pass
