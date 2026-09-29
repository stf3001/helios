"""L'élagage du crawler — la partie qui SUPPRIME, donc celle qu'il faut tenir.

Le crawler ne savait qu'ajouter : une fiche retirée d'un fichier markdown restait en base
pour toujours, listée sur /faq sans page pré-rendue derrière (lien mort), et toujours
servable par le chat. L'élagage corrige ça, mais il introduit le seul endroit du projet où
des fiches disparaissent toutes seules — d'où ces tests.

Il n'y a pas de base de données dans cette suite : on teste donc le GARDE-FOU, qui est ce
qui peut faire des dégâts, et la condition amont qui le déclenche. La suppression elle-même
est vérifiée à la main sur la vraie base (29/09/2026 : la fiche « Pourquoi installer
plusieurs éoliennes » est bien partie, sans laisser de chunk orphelin).
"""

import asyncio

import pytest

from app.services.agents_engine import SOURCES, _REPO_ROOT, _elaguer, parse_faq_markdown


class SessionQuiExplose:
    """Toute requête ou suppression fait échouer le test : rien ne doit partir en base."""

    async def scalars(self, *args, **kwargs):
        raise AssertionError("aucune requête ne doit partir quand le fichier est vide")

    async def delete(self, *args, **kwargs):
        raise AssertionError("rien ne doit être supprimé quand le fichier est vide")


def test_un_fichier_vide_n_elague_rien():
    """LE garde-fou : un parsing cassé ne doit pas effacer la source entière.

    Si l'expression de parsing se casse ou si le fichier devient illisible, `entries` est
    vide. Sans ce garde-fou, l'élagage en conclurait que TOUTES les fiches de la source ont
    disparu et les supprimerait — silencieusement. Mieux vaut une fiche périmée de trop
    qu'une source évaporée.
    """
    retires = asyncio.run(_elaguer(SessionQuiExplose(), SOURCES[0], set()))
    assert retires == 0


@pytest.mark.parametrize("source", [s for s in SOURCES if s.kind == "faq_markdown"],
                         ids=lambda s: s.name)
def test_chaque_source_declaree_produit_des_fiches(source):
    """La condition qui arme l'élagage : chaque source doit vraiment donner des fiches.

    C'est la protection en amont. Un chemin faux, un fichier renommé ou un format cassé se
    voient ici, au lieu de se manifester plus tard par un élagage évité de justesse (ou par
    une source absente du site sans que personne ne le remarque).
    """
    chemin = _REPO_ROOT / source.location
    assert chemin.exists(), f"{source.name} : fichier introuvable ({source.location})"

    fiches = parse_faq_markdown(chemin.read_text(encoding="utf-8"))
    assert fiches, f"{source.name} : le fichier existe mais ne produit aucune fiche"

    titres = [f["titre"] for f in fiches]
    assert len(titres) == len(set(titres)), (
        f"{source.name} : deux fiches portent le même intitulé — l'upsert se fait sur "
        f"(source, titre), l'une écraserait l'autre"
    )
