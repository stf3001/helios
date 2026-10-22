"""Pré-audit lot 7 : l'unité de la consommation d'une autre énergie (fioul, gaz, bois, réseau)

`conso_autre_energie_unite` : l'unité de `conso_autre_energie_qte` (`litres`, `kwh`, `m3`,
`steres`, `kg`). `conso_autre_energie_type` reste une chaîne de 50 caractères, mais ses anciennes
valeurs libres sont ramenées à la liste fermée (`gaz`, `fioul`, `bois_buches`, `granules`,
`reseau`) quand le texte est sans ambiguïté, sinon mises à NULL — « bois » seul ne dit pas
bûches ou granulés, « propane » n'est pas une énergie du moteur. Aucune unité n'est devinée :
une quantité ancienne reste sans unité, donc inutilisée. Réversible (la colonne d'unité part ;
un texte libre mis à NULL ne revient pas).

Revision ID: 0043_autre_energie_unite
Revises: 0042_vigilance
Create Date: 2026-10-22
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0043_autre_energie_unite"
down_revision: Union[str, None] = "0042_vigilance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def type_ramene(texte: str | None) -> str | None:
    """L'ancienne saisie libre, ramenée à la liste quand elle est sans ambiguïté."""
    if not texte:
        return None
    t = "".join(c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn")
    if "propane" in t or "butane" in t:
        return None
    trouves = {code for code, mots in (
        ("fioul", ("fioul", "fuel", "mazout")), ("gaz", ("gaz",)), ("granules", ("granule", "pellet")),
        ("bois_buches", ("buche", "stere")), ("reseau", ("reseau", "chaleur urbain")),
    ) if any(m in t for m in mots)}
    return trouves.pop() if len(trouves) == 1 else None


def upgrade() -> None:
    op.add_column("houses", sa.Column("conso_autre_energie_unite", sa.String(10)))
    bind = op.get_bind()
    lignes = bind.execute(sa.text(
        "SELECT id, conso_autre_energie_type FROM houses WHERE conso_autre_energie_type IS NOT NULL")).all()
    for id_, texte in lignes:
        nouveau = type_ramene(texte)
        if nouveau != texte:
            bind.execute(sa.text("UPDATE houses SET conso_autre_energie_type = :t WHERE id = :i"),
                         {"t": nouveau, "i": id_})


def downgrade() -> None:
    op.drop_column("houses", "conso_autre_energie_unite")
