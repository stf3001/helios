"""La mémoire de conversation du chat — sans réseau ni base de données.

Jusqu'au 02/10/2026, Helios recevait la constitution, les fiches trouvées, la fiche du
foyer et ses études, puis la question SEULE : dans une conversation, il ne se souvenait de
rien. Et la recherche vectorisait cette même question seule, donc une relance qui ne nomme
pas son sujet (« et dans le nord ? ») ne retrouvait plus rien.

Deux pièces réparent cela, et ce fichier les tient :

  `build_historique_context` — les derniers tours, posés dans le prompt ;
  `question_pour_recherche`  — la question enrichie, qui ne sert QU'À la recherche.

L'invariant à ne pas assouplir : **ce qui est enrichi ne sort jamais de la recherche**. La
question affichée, enregistrée et posée au modèle reste le texte du visiteur.
"""

from app.services import rag


class FauxMessage:
    """Juste ce que `rag` lit d'un message : son rôle, son texte, sa voie de réponse."""

    def __init__(self, role: str, content: str, model_used: str | None = None):
        self.role = role
        self.content = content
        self.model_used = model_used


def echange(question: str, reponse: str = "(réponse d'Helios)") -> list[FauxMessage]:
    return [FauxMessage("user", question), FauxMessage("helios", reponse, "api")]


# --------------------------------------------------------------- l'historique


def test_sans_historique_aucun_bloc():
    """Premier message d'une conversation : rien à relire, donc rien à poser dans le prompt."""
    assert rag.build_historique_context([]) is None


def test_historique_garde_l_ordre_et_distingue_les_voix():
    bloc = rag.build_historique_context(
        echange("c'est quoi un puits canadien", "un tuyau enterré") + echange("et l'hiver ?", "il préchauffe")
    )
    assert bloc is not None
    assert bloc.index("c'est quoi un puits canadien") < bloc.index("et l'hiver ?")
    assert "Visiteur : c'est quoi un puits canadien" in bloc
    assert "Toi (Helios) : un tuyau enterré" in bloc


def test_une_reponse_longue_est_tronquee_mais_pas_la_question():
    """On garde CE qu'Helios a dit, pas la façon dont il l'a dit — le prompt du modèle local
    est déjà long. Les questions du visiteur, courtes et porteuses du contexte, sont entières."""
    question = "q" * 600
    bloc = rag.build_historique_context(echange(question, "r" * 1200))
    assert question in bloc
    assert "r" * (rag.HISTORIQUE_REPONSE_MAX + 1) not in bloc
    assert "[…]" in bloc


# ----------------------------------------------------- la question enrichie


def test_une_question_longue_n_est_jamais_enrichie():
    """Elle porte son sujet toute seule ; y recoller le tour précédent ne ferait que diluer.

    Mesuré le 01/10/2026 : « à partir de quelle lettre je ne peux plus louer ? » (48 car.),
    posée après « c'est quoi le DPE », trouvait la BONNE fiche seule (0,670) et la perdait
    une fois enrichie. C'est ce cas qui a fixé le seuil à 45 caractères.
    """
    longue = "a partir de quelle lettre je ne peux plus louer mon logement ?"
    assert len(longue) >= rag.RELANCE_MAX_CARACTERES
    assert rag.question_pour_recherche(longue, echange("c'est quoi le DPE")) == longue


def test_une_relance_courte_recupere_le_sujet_du_tour_precedent():
    enrichie = rag.question_pour_recherche("et l'hiver ?", echange("c'est quoi un puits canadien"))
    assert "puits canadien" in enrichie
    assert "et l'hiver ?" in enrichie


def test_une_relance_sur_une_relance_garde_le_sujet():
    """DEUX questions d'ancrage, pas une.

    Trouvé en testant une vraie conversation : au troisième tour, la question précédente
    était elle-même une relance (« et ça marche dans le nord ? ») et ne nommait plus le
    sujet. Le puits canadien disparaissait de la recherche.
    """
    precedents = echange("c'est quoi un puits canadien") + echange("et ca marche dans le nord ?")
    enrichie = rag.question_pour_recherche("combien ca coute ?", precedents)
    assert "puits canadien" in enrichie
    assert "combien ca coute ?" in enrichie


def test_une_relance_sans_tour_precedent_reste_elle_meme():
    assert rag.question_pour_recherche("et l'hiver ?", []) == "et l'hiver ?"


def test_l_enrichissement_ne_sort_jamais_de_la_recherche():
    """L'invariant : le texte du visiteur n'est pas réécrit, il est seulement complété POUR
    chercher. Ce que la fonction rend contient donc toujours la question telle quelle."""
    question = "et le prix ?"
    assert question in rag.question_pour_recherche(question, echange("parle moi du solaire"))


# ------------------------------------------- le garde-fou de la réponse instantanée


class FauxDocument:
    source = "puits_canadien"


class FauxChunk:
    content = "### Q: une question\nR: la réponse de la fiche"


def resultat(score: float) -> list[dict]:
    return [{"score": score, "document": FauxDocument(), "chunk": FauxChunk()}]


def test_une_relance_exige_plus_de_certitude_pour_une_reponse_toute_faite():
    """Servir une fiche sans passer par le modèle est l'action la plus engageante du chat :
    personne ne rattrape une erreur de recherche. Sur une relance, le sujet est SUPPOSÉ et
    non écrit — on exige donc davantage.

    Mesuré : « et mes panneaux solaires ? », posée après une question sur le puits canadien,
    remontait la fiche du PUITS à 0,661, juste au-dessus du seuil normal. Helios aurait servi
    une réponse sur le puits canadien à quelqu'un qui parlait de panneaux.
    """
    entre_deux = resultat(0.661)
    assert rag.instant_answer(entre_deux) is not None
    assert rag.instant_answer(entre_deux, relance=True) is None


def test_une_relance_tres_sure_garde_sa_reponse_instantanee():
    """Le garde-fou ne doit pas supprimer la voie gratuite : les bonnes relances mesurées
    (coût 0,739, permis 0,708, hiver 0,731, entretien 0,786) restent instantanées."""
    for score in (0.708, 0.731, 0.739, 0.786):
        assert rag.instant_answer(resultat(score), relance=True) is not None


def test_le_seuil_de_relance_est_plus_haut_que_le_seuil_normal():
    from app.core.config import settings

    assert rag.RELANCE_INSTANT_MIN > settings.rag_instant_answer_threshold
