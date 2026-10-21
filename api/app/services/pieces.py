"""Résumé des pièces de la maison — fonctions pures, sans accès à la base (carnet, lot 2).

Il additionne et compare ; il ne calcule NI déperdition, NI puissance nécessaire, NI
recommandation d'émetteur. Un écart avec la fiche est signalé, jamais corrigé.

Statut de chaque valeur : `declare` (saisi par le foyer, pièces ou fiche), `calcule`
(somme, compte ou écart que nous en tirons).
"""

# Au-delà, la somme des pièces et la surface de la fiche ne racontent plus la même maison.
SEUIL_ECART_SURFACE = 0.15
# La surface habitable exclut le garage : il n'entre pas dans la comparaison.
_HORS_SURFACE_HABITABLE = ("garage",)


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _fmt_m2(x: float) -> str:
    return f"{round(x):d}" if abs(x - round(x)) < 0.05 else f"{x:.1f}".replace(".", ",")


def resume_pieces(house, pieces, emetteurs) -> dict:
    par_piece: dict = {}
    for e in emetteurs:
        par_piece.setdefault(_champ(e, "piece_id"), []).append(e)

    chauffees = [p for p in pieces if _champ(p, "chauffee") is not False]

    # Surface : comparée à la fiche seulement si TOUTES les pièces habitables ont la leur —
    # une somme partielle ferait toujours « trop petit ».
    habitables = [p for p in pieces if _champ(p, "type") not in _HORS_SURFACE_HABITABLE]
    surfaces = [_champ(p, "surface_m2") for p in habitables]
    connues = [s for s in surfaces if s]
    total = round(sum(connues), 1) if connues else None
    fiche_m2 = _champ(house, "surface_habitable")
    ecart_surface = None
    if total and fiche_m2 and len(connues) == len(habitables):
        ecart = (total - fiche_m2) / fiche_m2
        if abs(ecart) > SEUIL_ECART_SURFACE:
            ecart_surface = {
                "pieces_m2": total, "fiche_m2": fiche_m2, "ecart_pct": round(ecart * 100), "statut": "calcule",
                "message": f"La somme de vos pièces fait {_fmt_m2(total)} m², votre fiche indique {fiche_m2} m².",
            }

    # Émetteurs par type : puissance totale seulement si chaque ligne donne la sienne.
    agreges: dict = {}
    for e in emetteurs:
        a = agreges.setdefault(_champ(e, "type"), {"nombre": 0, "puissance": 0.0, "complete": True})
        nombre = _champ(e, "nombre") or 1
        a["nombre"] += nombre
        if _champ(e, "puissance_w"):
            a["puissance"] += nombre * _champ(e, "puissance_w")
        else:
            a["complete"] = False
    emetteurs_par_type = [
        {"type": t, "nombre": a["nombre"], "puissance_totale_w": round(a["puissance"]) if a["complete"] else None,
         "statut": "calcule"}
        for t, a in sorted(agreges.items(), key=lambda kv: -kv[1]["nombre"])
    ]

    sans_emetteur = [_champ(p, "nom") for p in chauffees if not par_piece.get(_champ(p, "id"))]

    nb_clim = sum(
        1 for p in pieces
        if any(_champ(e, "type") == "unite_interieure_clim" for e in par_piece.get(_champ(p, "id"), []))
    )
    fiche_clim = _champ(house, "clim_nb_pieces")
    ecart_clim = None
    if fiche_clim is not None and fiche_clim != nb_clim:
        ecart_clim = {
            "pieces": nb_clim, "fiche": fiche_clim, "statut": "calcule",
            "message": (f"{nb_clim} pièce{'s' if nb_clim > 1 else ''} avec une unité de climatisation, "
                        f"votre fiche en indique {fiche_clim}."),
        }

    return {
        "nb_pieces": {"valeur": len(pieces), "statut": "calcule"},
        "nb_chauffees": {"valeur": len(chauffees), "statut": "calcule"},
        "surface_pieces_m2": {"valeur": total, "statut": "calcule",
                              "pieces_sans_surface": len(habitables) - len(connues)},
        "surface_fiche_m2": {"valeur": fiche_m2, "statut": "declare"},
        "ecart_surface": ecart_surface,
        "emetteurs_par_type": emetteurs_par_type,
        "chauffees_sans_emetteur": {"valeur": sans_emetteur, "statut": "calcule"},
        "pieces_avec_clim": {"valeur": nb_clim, "statut": "calcule"},
        "clim_fiche": {"valeur": fiche_clim, "statut": "declare"},
        "ecart_clim": ecart_clim,
    }
