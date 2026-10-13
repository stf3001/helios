"""L'empreinte du contenu — ce qui décide si une fiche a VRAIMENT changé (migration 0022).

Pourquoi ces tests existent : le crawler écrivait `date_maj = today` à chaque passage, que le
contenu ait bougé ou non. Deux conséquences, dont la seconde est passée inaperçue des mois.

1. Chaque crawl ré-embarquait toute la base — la seule opération coûteuse de l'ingestion.
2. Surtout, `date_maj` ne voulait plus rien dire, et la veille, qui s'en sert pour repérer les
   contenus périmés, ne pouvait STRUCTURELLEMENT rien signaler : son compteur était remis à
   zéro à chaque passage. Le « 0 document périmé » du journal était la seule réponse possible.

L'INVARIANT TENU ICI : un crawl n'écrit jamais `date_maj` sans que l'empreinte ait bougé, et
n'appelle jamais l'embedding pour un contenu identique. Ne pas l'assouplir — le jour où il
cède, rien ne tombe en panne visiblement, la veille redevient simplement muette.

Aucune base de données et aucun appel à Ollama : la session et l'embedding sont remplacés,
et c'est justement le compteur d'appels à l'embedding qui porte l'essentiel du test.
"""

import asyncio
from datetime import date

import pytest

from app.models.kb import KbChunk, KbDocument
from app.services import agents_engine as ae

CONTENU = "Q: Faut-il isoler avant de poser des panneaux ?\nR: Oui, dans cet ordre."
TITRE = "Faut-il isoler avant de poser des panneaux ?"


class SessionFactice:
    """Juste assez d'une session pour faire tourner `crawl_source` hors base.

    Le choix de ce que renvoie `scalar` se fait sur la table visée dans la requête, et non
    sur l'ordre des appels : le test ne doit pas se casser si l'ordre change dans le code.
    """

    def __init__(self, doc: KbDocument | None = None, chunk: KbChunk | None = None):
        self.doc, self.chunk = doc, chunk
        self.ajoutes: list = []
        self.commits = 0

    async def scalar(self, stmt):
        return self.chunk if "kb_chunks" in str(stmt) else self.doc

    async def scalars(self, stmt):
        return []  # l'élagage ne trouve rien à retirer

    def add(self, obj):
        self.ajoutes.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        self.commits += 1


@pytest.fixture
def source_factice(monkeypatch):
    """Une source qui rend une fiche connue, sans toucher au disque, et compte les embeddings."""
    appels_embed: list[str] = []

    async def _faux_fetch(source):
        return [{
            "titre": TITRE,
            "content": CONTENU,
            "metadata": {"cat": "isolation", "tags": [], "verif": None,
                         "niveau_confiance": source.fiabilite},
            "fiabilite": source.fiabilite,
            "valide_brut": None,
            "zone": None,
        }]

    async def _faux_embed(texte):
        appels_embed.append(texte)
        return [0.0] * 1024

    monkeypatch.setattr(ae, "_fetch_source_entries", _faux_fetch)
    monkeypatch.setattr(ae, "embed", _faux_embed)
    return appels_embed


def _spec(**kw) -> ae.SourceSpec:
    return ae.SourceSpec(name="source_test", kind="faq_markdown", location="néant", **kw)


def _doc_en_base(empreinte: str | None, date_maj: date) -> KbDocument:
    return KbDocument(source="source_test", titre=TITRE, date_maj=date_maj,
                      statut="actif", empreinte=empreinte)


def test_contenu_inchange_n_embarque_rien_et_ne_touche_pas_date_maj(source_factice):
    """LE test. Même contenu qu'au passage précédent : aucun embedding, `date_maj` intacte."""
    veille_date = date(2026, 1, 15)
    doc = _doc_en_base(ae._empreinte(CONTENU), veille_date)
    session = SessionFactice(doc, KbChunk(content=CONTENU))

    res = asyncio.run(ae.crawl_source(session, _spec()))

    assert source_factice == [], "un contenu identique ne doit JAMAIS être ré-embarqué"
    assert doc.date_maj == veille_date, "date_maj est la date du dernier CHANGEMENT de contenu"
    assert doc.date_crawl == date.today(), "le passage, lui, doit être noté"
    assert res["unchanged"] == 1 and res["updated"] == 0 and res["added"] == 0


def test_contenu_modifie_est_reembarque_et_date_maj_avance(source_factice):
    """L'autre moitié de l'invariant : un vrai changement doit bien tout rafraîchir."""
    doc = _doc_en_base("une_empreinte_qui_ne_correspond_plus", date(2026, 1, 15))
    chunk = KbChunk(content="ancien contenu")
    session = SessionFactice(doc, chunk)

    res = asyncio.run(ae.crawl_source(session, _spec()))

    assert source_factice == [CONTENU], "le contenu a changé : il faut un nouvel embedding"
    assert doc.date_maj == date.today()
    assert doc.empreinte == ae._empreinte(CONTENU)
    assert chunk.content == CONTENU
    assert res["updated"] == 1 and res["unchanged"] == 0


def test_document_sans_empreinte_est_embarque_une_fois(source_factice):
    """Les fiches ingérées avant la migration : une fois, puis plus jamais sans raison."""
    doc = _doc_en_base(None, date(2026, 1, 15))
    session = SessionFactice(doc, KbChunk(content=CONTENU))

    asyncio.run(ae.crawl_source(session, _spec()))

    assert source_factice == [CONTENU]
    assert doc.empreinte == ae._empreinte(CONTENU)


def test_un_document_sans_chunk_est_refait_meme_si_l_empreinte_colle(source_factice):
    """Garde-fou : un document sans chunk est introuvable par la recherche, donc invisible.

    Le raccourci « empreinte identique, on passe » ne doit pas laisser un document muet dans
    la base sous prétexte que son empreinte est à jour.
    """
    doc = _doc_en_base(ae._empreinte(CONTENU), date(2026, 1, 15))
    session = SessionFactice(doc, chunk=None)

    asyncio.run(ae.crawl_source(session, _spec()))

    assert source_factice == [CONTENU]
    assert any(isinstance(o, KbChunk) for o in session.ajoutes)


def test_la_fiabilite_suit_la_declaration_de_la_source(source_factice):
    """Reclasser une source doit s'appliquer sans avoir à modifier les fiches elles-mêmes."""
    doc = _doc_en_base(ae._empreinte(CONTENU), date(2026, 1, 15))
    session = SessionFactice(doc, KbChunk(content=CONTENU))

    asyncio.run(ae.crawl_source(session, _spec(fiabilite="officiel")))

    assert doc.fiabilite == "officiel"
    assert source_factice == [], "un reclassement ne justifie pas de recalculer un vecteur"


# --- Fin de validité ------------------------------------------------------------------

def test_la_date_de_la_fiche_prime_sur_la_cadence_de_la_source():
    entry = {"titre": TITRE, "valide_brut": "2027-06-30"}
    validite, anomalie = ae._valide_jusqu_au(_spec(validite_mois=12), entry, date(2026, 3, 1))
    assert validite == date(2027, 6, 30), "une date écrite est un fait, pas une cadence"
    assert anomalie is None


def test_la_cadence_de_la_source_sert_de_defaut():
    entry = {"titre": TITRE, "valide_brut": None}
    validite, anomalie = ae._valide_jusqu_au(_spec(validite_mois=12), entry, date(2026, 3, 15))
    assert validite == date(2027, 3, 15)
    assert anomalie is None


def test_sans_date_ni_cadence_il_n_y_a_pas_de_peremption():
    validite, anomalie = ae._valide_jusqu_au(_spec(), {"titre": TITRE, "valide_brut": None},
                                             date(2026, 3, 15))
    assert validite is None and anomalie is None


def test_une_date_mal_ecrite_est_signalee_jamais_devinee():
    """Mieux vaut aucune fin de validité qu'une péremption inventée depuis une faute de frappe."""
    entry = {"titre": TITRE, "valide_brut": "30/06/2027"}
    validite, anomalie = ae._valide_jusqu_au(_spec(validite_mois=12), entry, date(2026, 3, 1))
    assert validite is None
    assert anomalie is not None and "30/06/2027" in anomalie


def test_ajoute_mois_ramene_au_dernier_jour_du_mois():
    """31 janvier + 1 mois n'existe pas : on ne doit pas lever, mais atterrir en février."""
    assert ae._ajoute_mois(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert ae._ajoute_mois(date(2024, 1, 31), 1) == date(2024, 2, 29)  # année bissextile
    assert ae._ajoute_mois(date(2026, 3, 15), 12) == date(2027, 3, 15)
    assert ae._ajoute_mois(date(2026, 12, 1), 1) == date(2027, 1, 1)   # passage d'année


def test_toute_source_declare_une_fiabilite_connue():
    """Un libellé inventé passerait inaperçu : il n'y a pas de contrainte en base."""
    connues = {"officiel", "maison", "constructeur", "hypothese", "pedagogique", "veille"}
    for s in ae.SOURCES:
        assert s.fiabilite in connues, f"{s.name} : fiabilité « {s.fiabilite} » inconnue"
