"""Résumé des pièces (carnet, lot 2) — sans base."""

from app.services.pieces import resume_pieces


def _p(id_, surface, type_="chambre", chauffee=True, nom=None):
    return {"id": id_, "nom": nom or id_, "type": type_, "surface_m2": surface, "chauffee": chauffee}


def _e(piece_id, type_="radiateur_eau", nombre=1, puissance=None):
    return {"piece_id": piece_id, "type": type_, "nombre": nombre, "puissance_w": puissance}


def test_ecart_de_surface_signale_au_dela_de_15_pct():
    pieces = [_p("a", 50), _p("b", 50)]  # 100 m²
    assert resume_pieces({"surface_habitable": 116}, pieces, [])["ecart_surface"] is None  # 13,8 %
    assert resume_pieces({"surface_habitable": 86}, pieces, [])["ecart_surface"] is not None  # +16,3 %
    # 14 % et 16 % pile, de chaque côté.
    assert resume_pieces({"surface_habitable": 100}, [_p("a", 114)], [])["ecart_surface"] is None
    ecart = resume_pieces({"surface_habitable": 100}, [_p("a", 84)], [])["ecart_surface"]
    assert ecart["ecart_pct"] == -16 and ecart["statut"] == "calcule"
    assert ecart["message"] == "La somme de vos pièces fait 84 m², votre fiche indique 100 m²."


def test_pas_de_comparaison_si_une_surface_manque_et_garage_exclu():
    r = resume_pieces({"surface_habitable": 110}, [_p("a", 40), _p("b", None)], [])
    assert r["ecart_surface"] is None and r["surface_pieces_m2"]["pieces_sans_surface"] == 1
    r = resume_pieces({"surface_habitable": 100}, [_p("a", 100), _p("g", 30, type_="garage")], [])
    assert r["surface_pieces_m2"]["valeur"] == 100 and r["ecart_surface"] is None


def test_puissance_totale_nulle_si_une_puissance_manque():
    pieces = [_p("a", 20), _p("b", 15)]
    complet = resume_pieces({}, pieces, [_e("a", nombre=2, puissance=1000), _e("b", puissance=750)])
    assert complet["emetteurs_par_type"] == [
        {"type": "radiateur_eau", "nombre": 3, "puissance_totale_w": 2750, "statut": "calcule"}]
    partiel = resume_pieces({}, pieces, [_e("a", nombre=2, puissance=1000), _e("b")])
    assert partiel["emetteurs_par_type"][0]["puissance_totale_w"] is None


def test_piece_chauffee_sans_emetteur():
    pieces = [_p("a", 20, nom="Séjour"), _p("b", 10, nom="Chambre 2"), _p("c", 5, nom="Cellier", chauffee=False)]
    r = resume_pieces({}, pieces, [_e("a")])
    assert r["chauffees_sans_emetteur"]["valeur"] == ["Chambre 2"]
    assert r["nb_chauffees"]["valeur"] == 2


def test_ecart_clim_avec_la_fiche():
    pieces = [_p("a", 20), _p("b", 10)]
    emetteurs = [_e("a", type_="unite_interieure_clim"), _e("a", type_="unite_interieure_clim"), _e("b")]
    r = resume_pieces({"clim_nb_pieces": 2}, pieces, emetteurs)
    assert r["pieces_avec_clim"]["valeur"] == 1  # deux unités, une seule pièce
    assert r["ecart_clim"]["fiche"] == 2 and r["clim_fiche"]["statut"] == "declare"
    assert resume_pieces({"clim_nb_pieces": 1}, pieces, emetteurs)["ecart_clim"] is None
    assert resume_pieces({"clim_nb_pieces": None}, pieces, emetteurs)["ecart_clim"] is None
