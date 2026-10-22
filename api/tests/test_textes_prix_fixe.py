"""Mises en relation, lot 1 : tous les textes publics décrivent le prix fixe.

Plus aucun « commission » au sens des travaux dans `frontend/src` ni dans `kb/`. Restent permis,
et nommés ici : le courtage et l'achat d'énergie (modèle inchangé), les institutions (Commission
européenne, Commission de régulation de l'énergie), et les textes du prix fixe qui disent
justement « sans commission ».
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
FRONT = RACINE / "frontend" / "src"

COURT = ("HELIOS est gratuit pour vous, toujours. Quand vous demandez à être mis en relation avec une entreprise "
         "partenaire, celle-ci paie à HELIOS un prix fixe, le même quel que soit le montant de vos travaux, même si "
         "vous ne signez rien. Nos conseils n'en dépendent pas.")
TRANSPARENCE = ("Chaque entreprise partenaire paie à HELIOS un prix fixe pour chaque mise en relation demandée par un "
                "foyer, sans commission sur les travaux. HELIOS n'a donc aucun intérêt à ce que vous dépensiez plus, ni "
                "à vous orienter vers une entreprise plutôt qu'une autre.")
DEVENIR = ("60 € HT par mise en relation, demandée par un foyer, avec son projet et son consentement. Pas "
           "d'abonnement, pas de commission sur vos chantiers. Contestation possible sous 7 jours : coordonnées "
           "fausses, hors de votre zone ou de vos métiers, doublon, foyer injoignable après trois essais.")

# Le courtage et l'achat d'énergie gardent leur modèle (hors de ce lot).
FICHIERS_COURTAGE = {"pages/AchatEnergie.tsx", "pages/EspaceEnergie.tsx", "achat_energie.md", "pilotage.md",
                     "action_contrat.md"}
PERMIS = re.compile(r"commission (europ[ée]enne|de r[ée]gulation)|sans commission sur les travaux|"
                    r"pas de commission sur vos chantiers|r[ée]mun[ée]ration du courtier", re.I)


def _plat(chemin: Path) -> str:
    return " ".join(chemin.read_text(encoding="utf-8").split())


def _occurrences():
    fichiers = [*FRONT.rglob("*.tsx"), *FRONT.rglob("*.ts"), *FRONT.rglob("*.json"), *(RACINE / "kb").glob("*.md")]
    for f in fichiers:
        rel = f.relative_to(FRONT).as_posix() if FRONT in f.parents else f.name
        if rel in FICHIERS_COURTAGE:
            continue
        texte = _plat(f)
        for m in re.finditer(r"commission", texte, re.I):
            contexte = texte[max(0, m.start() - 40): m.end() + 40]
            if not PERMIS.search(contexte):
                yield rel, contexte


def test_plus_de_commission_sur_les_travaux_dans_les_textes_publics():
    assert list(_occurrences()) == []


@pytest.mark.parametrize("fichier, texte", [
    ("components/layout/Footer.tsx", COURT),
    ("pages/Home.tsx", COURT),
    ("data/pagesFixes.json", COURT),
    ("pages/Partenaires.tsx", TRANSPARENCE),
    ("data/pagesFixes.json", TRANSPARENCE),
    ("pages/DevenirPartenaire.tsx", DEVENIR),
    ("data/pagesFixes.json", DEVENIR),
])
def test_les_textes_sont_recopies_tels_quels(fichier, texte):
    assert texte in _plat(FRONT / fichier)


def test_engagements_et_constitution():
    engagements = (FRONT / "pages" / "Engagements.tsx").read_text(encoding="utf-8")
    assert COURT in " ".join(re.sub(r'"\s*\+\s*"', "", engagements).split())
    constitution = _plat(RACINE / "prompts" / "constitution-v0.3.md")
    assert ("la plateforme est payée à prix fixe par les entreprises partenaires pour chaque mise en relation "
            "demandée, jamais par le foyer, et sans lien avec le montant des travaux") in constitution
    assert "commission de SOBRY" in constitution  # le courtage ne change pas
