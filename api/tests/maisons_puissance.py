"""Les quatre maisons du lot 6 du pré-audit (puissance de chauffage et radiateurs).

Partagées par `test_audit_puissance.py` et par le script qui a enregistré leur sortie v2.5
(`tests/fixtures/audit_v25/`), pour prouver que la v2.6 ne change rien d'autre.
"""
from types import SimpleNamespace

from tests.test_audit_engine import maison_type, reference_complete


def piece(nom, type_, surface, *emetteurs, chauffee=True):
    """Une pièce et ses émetteurs `(type, nombre, puissance_w)`, comme la base les rend."""
    p = SimpleNamespace(id=f"p-{nom}", nom=nom, type=type_, surface_m2=surface, chauffee=chauffee)
    es = [SimpleNamespace(piece_id=p.id, type=t, nombre=n, puissance_w=w) for t, n, w in emetteurs]
    return p, es


def pieces_fioul():
    """Six pièces chauffées (90 m²) et un garage, radiateurs à eau donnés pour ΔT = 50 K ; la salle
    de bains sans puissance, le bureau en plancher chauffant. Un verdict de chaque sorte."""
    lignes = [
        piece("Séjour", "sejour", 35, ("radiateur_eau", 2, 2500)),
        piece("Cuisine", "cuisine", 12, ("radiateur_eau", 1, 1000)),
        piece("Chambre 1", "chambre", 14, ("radiateur_eau", 1, 2500)),
        piece("Chambre 2", "chambre", 12, ("radiateur_eau", 1, 1800)),
        piece("Bureau", "bureau", 10, ("plancher_chauffant_eau", 1, None)),
        piece("Salle de bains", "salle_de_bain", 7, ("radiateur_eau", 1, None)),
        piece("Garage", "garage", 20, chauffee=False),
    ]
    return [p for p, _ in lignes], [e for _, es in lignes for e in es]


def maisons():
    """Nom → (maison, pièces, émetteurs)."""
    pieces, emetteurs = pieces_fioul()
    return {
        "reference": (reference_complete(), [], []),
        "fioul_6_pieces": (maison_type(), pieces, emetteurs),
        "convecteurs": (maison_type(chauffage_principal="elec_direct", conso_elec_kwh_an=12000), [], []),
        "gaz_sans_pieces": (maison_type(chauffage_principal="gaz"), [], []),
    }
