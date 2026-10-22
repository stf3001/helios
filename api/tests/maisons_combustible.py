"""Les cas du lot 7 du pré-audit (consommation de fioul, de gaz et de bois lue avec son unité).

Partagés par `test_audit_combustible.py` et par le script qui a enregistré leur sortie v2.6
(`tests/fixtures/audit_v26/`). La v2.6 ignorait la quantité déclarée : sa sortie est celle
de la maison sans relevé, plus une hypothèse « non utilisée ».
"""
from tests.maisons_puissance import maisons as maisons_lot6
from tests.test_audit_engine import maison_type, reference_complete

# Nom → champs de la fiche. `conso_autre_energie_unite` n'existait pas en v2.6.
CAS = {
    "fioul_1500_litres": dict(chauffage_principal="fioul", conso_autre_energie_type="fioul",
                              conso_autre_energie_qte=1500, conso_autre_energie_unite="litres"),
    "gaz_12000_kwh_ecs_gaz": dict(chauffage_principal="gaz", ecs="gaz", nb_occupants=3,
                                  conso_autre_energie_type="gaz", conso_autre_energie_qte=12000,
                                  conso_autre_energie_unite="kwh"),
    "gaz_1100_m3": dict(chauffage_principal="gaz", conso_autre_energie_type="gaz",
                        conso_autre_energie_qte=1100, conso_autre_energie_unite="m3"),
    "bois_8_steres": dict(chauffage_principal="bois", conso_autre_energie_type="bois_buches",
                          conso_autre_energie_qte=8, conso_autre_energie_unite="steres"),
    "fioul_sans_releve": dict(chauffage_principal="fioul"),
}


def cas(nom: str, avec_unite: bool = True):
    champs = dict(CAS[nom])
    if not avec_unite:
        champs.pop("conso_autre_energie_unite", None)
    return maison_type(**champs)


def maisons_v26():
    """Les maisons dont la sortie v2.6 est enregistrée : les quatre du lot 6 (dont la référence
    et son appoint « autre », le cas du point 80) et les cas ci-dessus, sans unité."""
    sortie = {nom: (h, p, e) for nom, (h, p, e) in maisons_lot6().items()}
    sortie.update({nom: (cas(nom, avec_unite=False), [], []) for nom in CAS})
    return sortie


REFERENCE = reference_complete
