"""Ce qu'Helios a sous les yeux quand on lui demande un professionnel.

Le risque n'est pas qu'il oublie l'annuaire : c'est qu'il s'en serve pour POUSSER un
partenaire. La charte l'interdit — « proposer un partenaire sans votre accord » figure
noir sur blanc dans ce qu'Helios ne fait jamais. Ces tests gardent donc la regle autant
que les noms.
"""

from app.services import rag


def test_le_bloc_porte_les_partenaires_de_la_zone():
    bloc = rag.build_partenaires_context(
        {"solaire": ["AD Solar", "Luberon Solaire"], "pac": ["Luberon Thermique"]}, "13")
    assert "AD Solar" in bloc
    assert "Luberon Solaire" in bloc
    assert "Luberon Thermique" in bloc
    assert "13" in bloc


def test_le_bloc_rappelle_la_regle_de_la_charte_a_cote_des_noms():
    """La regle doit etre DANS le bloc, pas seulement dans la constitution.

    Un petit modele perd de vue une consigne enterree trente lignes plus haut. Celle-ci
    doit se trouver a cote des noms, la ou elle sert.
    """
    bloc = rag.build_partenaires_context({"solaire": ["AD Solar"]}, "13")
    assert "QUE si le visiteur demande" in bloc
    assert "Jamais de toi-même" in bloc


def test_sans_departement_helios_demande_le_code_postal():
    """Un visiteur anonyme n'a pas de zone : on ne cite personne au hasard."""
    bloc = rag.build_partenaires_context({}, None)
    assert "code postal" in bloc
    assert "AD Solar" not in bloc


def test_tous_les_partenaires_d_un_metier_sont_cites_ensemble():
    """Un seul nom ressemble a une recommandation ; la liste laisse le choix."""
    bloc = rag.build_partenaires_context(
        {"isolation": ["Isolation Mistral", "Luberon Isolation", "Esterel Isolation"]}, "84")
    for nom in ("Isolation Mistral", "Luberon Isolation", "Esterel Isolation"):
        assert nom in bloc
    assert "donne-les TOUTES" in bloc


def test_le_bloc_entre_bien_dans_le_prompt_final():
    """Il doit arriver APRES la fiche du foyer et AVANT la question.

    C'est l'ordre voulu par `build_user_content` : les modeles locaux suivent ce qui est
    proche de la question, pas ce qui est enterre au debut.
    """
    bloc = rag.build_partenaires_context({"solaire": ["AD Solar"]}, "13")
    prompt = rag.build_user_content("qui peut me poser des panneaux ?", [],
                                    partenaires_context=bloc)
    assert "AD Solar" in prompt
    assert prompt.index("ANNUAIRE") < prompt.index("qui peut me poser des panneaux ?")
