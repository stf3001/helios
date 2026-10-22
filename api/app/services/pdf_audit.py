"""Génération du PDF de pré-audit — doc 07 §6.6.

Utilise fpdf2 (pur Python, aucune dépendance système). Le PDF ne fait que METTRE EN FORME le
JSON déterministe du moteur : aucun chiffre n'est (re)calculé ici, pas même une somme.

Polices : Plus Jakarta Sans (texte) et Instrument Serif (titres), celles du site, embarquées
en TTF statiques dans `app/assets/fonts/` avec leur licence OFL. Si un fichier manque, le
document retombe sur Helvetica, dont le jeu latin-1 n'a ni « € » ni « œ » : `_s()` les
remplace alors. Le PDF ne doit jamais échouer à cause d'une police.

Formats : les audits stockés ne sont jamais recalculés. Un audit v2.3 (présence de
`synthese.plan_recommande`) a sa mise en page en quatre parties ; les plus anciens gardent
leur structure, avec les mêmes polices, couleurs et règles d'affichage.
"""

import re
from datetime import date
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos
from fpdf.fonts import FontFace
from PIL import Image

from app.core.config import settings
from app.services import audit_reference as ref
from app.services.audit_engine import champs_supposes

PDF_DIR = Path(__file__).resolve().parents[2] / "generated" / "audits"
_LOGO_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "brand" / "logo-mark.png"
FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_POLICES = {
    ("sans", ""): "PlusJakartaSans-Regular.ttf",
    ("sans", "B"): "PlusJakartaSans-Bold.ttf",
    ("sans", "I"): "PlusJakartaSans-Italic.ttf",
    ("serif", ""): "InstrumentSerif-Regular.ttf",  # n'existe qu'en 400 : jamais de gras
}

# Copie de frontend/src/index.css (:root), les deux se tiennent à jour ENSEMBLE,
# comme frontend/src/data/couleurs.ts.
INK = (27, 42, 47)         # #1B2A2F — texte, titres
TEXTE_2 = (74, 90, 95)     # #4A5A5F — texte secondaire
ACCENT = (168, 66, 15)     # #A8420F — une action, la première étape
SABLE = (245, 239, 228)    # #F5EFE4 — fonds d'encadré
BORD = (226, 216, 198)     # #E2D8C6 — filets
VERT = (47, 122, 91)       # #2F7A5B — ce qui va bien, gestes gratuits
BLANC = (255, 255, 255)

# Étiquette énergie du DPE (modèle de l'arrêté du 31/03/2021). Lettre en blanc sauf sur
# les trois bandes claires, où le blanc ne se lit pas.
DPE_COULEURS = {"A": (0, 156, 109), "B": (82, 177, 83), "C": (120, 189, 118), "D": (244, 231, 15),
                "E": (240, 180, 15), "F": (235, 130, 53), "G": (215, 34, 31)}
DPE_LETTRE_ENCRE = {"C", "D", "E"}

NBSP = " "  # entre les milliers et devant €, %, kWh : un montant ne se coupe jamais
_ESPACE_MONTANT = re.compile(r"(?<=\d) (?=\d{3}\b|€|%|kWh|kVA|kg|ans\b|°C)")

_POSTE_LABEL = {
    "toiture": "Toiture / combles",
    "murs": "Murs",
    "air_ventilation": "Air / ventilation",
    "menuiseries": "Menuiseries",
    "plancher": "Plancher bas",
    "ponts_thermiques": "Ponts thermiques",
}
_ORIGINE = {
    "dpe": "d'après la lettre DPE",
    "annee_construction": "d'après l'année de construction",
    "defaut": "valeur par défaut, faute de DPE et d'année de construction",
}
_ORIGINE_PHRASE = {
    "dpe": "L'estimation part de la lettre DPE de votre fiche.",
    "annee_construction": ("Pas de lettre DPE dans votre fiche : l'estimation part de l'année de "
                           "construction et de l'état d'isolation que vous avez décrit."),
    "defaut": ("Ni lettre DPE ni année de construction dans votre fiche : l'estimation part de valeurs "
               "par défaut, à préciser."),
}
_ENERGIE = {"electricite": "électricité", "gaz": "gaz", "fioul": "fioul", "bois": "bois",
            "reseau": "réseau de chaleur"}
_HORIZON = {"maintenant": "Maintenant", "prioritaire": "Prioritaire", "a_l_occasion": "À l'occasion"}
_NIVEAU = {
    "conseils_generaux": "Conseils généraux",
    "prediagnostic_qualitatif": "Pré-diagnostic qualitatif",
    "preaudit_chiffre": "Pré-audit chiffré",
}
_STATUTS = ("Statuts : déclaré (vous l'avez dit), supposé (faute d'information), calculé (par le "
            "moteur), observé.")
_LEGENDE_RETOUR = ("au-delà de {max} ans, non rentable sur l'énergie seule : voir ses autres "
                   "bénéfices (confort, valeur du logement).")


# --- Texte et nombres -----------------------------------------------------------------------

def _s(text: str) -> str:
    """Repli Helvetica : rend une chaîne compatible latin-1 (€, œ, tirets, flèches...)."""
    remplacements = {"€": "EUR", "œ": "oe", "Œ": "OE", "’": "'", "…": "...", "–": "-", "—": "-",
                     "→": "->", "•": "-", "≥": ">=", "≤": "<="}
    for car, rempl in remplacements.items():
        text = (text or "").replace(car, rempl)
    return text.encode("latin-1", "replace").decode("latin-1")


def _milliers(n) -> str:
    return f"{int(round(n)):,}".replace(",", NBSP)


def _eur(n) -> str:
    return f"{_milliers(n)}{NBSP}€"


def _plage(f: dict) -> str:
    """Fourchette compacte, pour un tableau : « 1 500 – 2 500 € ». La seule coupure
    permise est après le tiret : une colonne étroite donne « 15 300 – » puis « 30 600 € »."""
    if f["bas"] == f["haut"]:
        return _eur(f["bas"])
    return f"{_milliers(f['bas'])}{NBSP}– {_milliers(f['haut'])}{NBSP}€"


def _plage_txt(f: dict) -> str:
    """Fourchette dans une phrase : « 1 500 à 2 500 € »."""
    if f["bas"] == f["haut"]:
        return _eur(f["bas"])
    return f"{_milliers(f['bas'])} à {_milliers(f['haut'])}{NBSP}€"


def _plage_aide(f) -> str:
    """Une aide nulle s'écrit « aucune » : « 0-0 » se lit comme un oubli."""
    if isinstance(f, (int, float)):  # audit v1 : un nombre
        return "aucune" if not f else f"~{_eur(f)}"
    return "aucune" if not f["bas"] and not f["haut"] else _plage(f)


def _montant(v) -> str:
    return _eur(v) if isinstance(v, (int, float)) else _plage(v)


def _dec(x, n: int = 1) -> str:
    """Décimale à la française : 0.2001 -> « 0,2001 », 4.1 -> « 4,1 »."""
    if x is None:
        return "–"
    texte = f"{x:.{n}f}" if isinstance(x, float) and n is not None else str(x)
    return texte.replace(".", ",")


def _pct(x) -> str:
    return "–" if x is None else f"{_dec(float(x))}{NBSP}%".replace(f",0{NBSP}%", f"{NBSP}%")


def _kwh(n) -> str:
    return f"{_milliers(n)}{NBSP}kWh"


def _retour_trop_long(a: dict) -> bool:
    r = a.get("temps_retour_ans")
    return r is not None and r > settings.audit_retour_affichage_max_ans


def _retour(a: dict) -> str:
    """Au-delà du seuil d'affichage, « > 30 ans » : 535 ans ne veut rien dire pour un lecteur."""
    r = a.get("temps_retour_ans")
    if r is None:
        return "–"
    if _retour_trop_long(a):
        return f">{NBSP}{settings.audit_retour_affichage_max_ans}{NBSP}ans"
    return f"{_dec(float(r))}{NBSP}ans"


def _date_aides(audit: dict) -> str:
    """Date du relevé des aides de CET audit, au format JJ/MM/AAAA.

    Les audits antérieurs à la v2.2 ne la portent pas : leurs aides venaient du relevé du
    22/07/2026, c'est donc la date qu'ils affichaient et qu'ils gardent.
    """
    iso = audit.get("aides_date_reference")
    return date.fromisoformat(iso).strftime("%d/%m/%Y") if iso else "22/07/2026"


def _libelle(champ: str, valeur) -> str:
    return ref.LIBELLE_VALEUR.get(champ, {}).get(valeur, str(valeur))


# --- Le document ----------------------------------------------------------------------------

class _AuditPDF(FPDF):
    def __init__(self, fonts_dir: Path):
        super().__init__()
        self.unicode = self._charger_polices(fonts_dir)
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=18)

    def _charger_polices(self, fonts_dir: Path) -> bool:
        fichiers = {cle: fonts_dir / nom for cle, nom in _POLICES.items()}
        if not all(f.exists() for f in fichiers.values()):
            return False
        try:
            for (famille, style), fichier in fichiers.items():
                self.add_font(famille, style, str(fichier))
        except Exception:  # police illisible : on ne bloque jamais le document pour ça
            return False
        return True

    def multi_cell(self, *args, **kwargs):
        kwargs.setdefault("align", "L")  # fpdf2 justifie par défaut : espaces étirés, illisible
        return super().multi_cell(*args, **kwargs)

    def normalize_text(self, text):
        # Les textes du moteur (fiches, conseils) s'écrivent avec des espaces simples : un
        # montant ne doit pas se couper pour autant (« 146 » en fin de ligne, « €/an » dessous).
        text = _ESPACE_MONTANT.sub(NBSP, text or "")
        return super().normalize_text(text if self.unicode else _s(text))

    def police(self, role: str = "sans", style: str = "", taille: float = 10):
        if self.unicode:
            self.set_font(role, "" if role == "serif" else style, taille)
        else:
            self.set_font("Helvetica", "B" if role == "serif" else style, taille * (0.85 if role == "serif" else 1))

    def header(self):
        y = 10
        if _LOGO_PATH.exists():
            logo_h = 8
            self.image(str(_LOGO_PATH), x=self.l_margin, y=y, h=logo_h)
            # Marque carrée depuis la refonte : on lit le rapport du fichier plutôt que de
            # l'écrire en dur, sinon le titre se décale le jour où le dessin change.
            with Image.open(_LOGO_PATH) as mark:
                ratio = mark.width / mark.height
            x = self.l_margin + logo_h * ratio + 3
        else:
            x = self.l_margin
        self.set_xy(x, y)
        self.police("serif", "", 17)
        self.set_text_color(*INK)
        self.cell(40, 8, "Helios")
        self.police("sans", "", 8.5)
        self.set_text_color(*TEXTE_2)
        self.set_xy(self.l_margin, y + 1)
        self.cell(0, 6, "Pré-audit énergétique indicatif", align="R")
        self.set_draw_color(*BORD)
        self.set_line_width(0.3)
        self.line(self.l_margin, y + 11, self.w - self.r_margin, y + 11)
        self.set_y(y + 16)
        self.set_text_color(*INK)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*BORD)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.police("sans", "", 7)
        self.set_text_color(*TEXTE_2)
        largeur = self.w - self.l_margin - self.r_margin
        self.cell(largeur - 20, 4, "Pré-diagnostic indicatif (ordres de grandeur), ne remplace ni un DPE ni un "
                                   "audit réalisé par un professionnel certifié.")
        self.cell(20, 4, f"{self.page_no()} / {{nb}}", align="R")
        self.set_text_color(*INK)


def _largeur(pdf: FPDF) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def _place(pdf: FPDF, hauteur: float):
    """Saute de page si `hauteur` mm ne tiennent plus : un bloc ne se coupe pas en deux."""
    if pdf.get_y() + hauteur > pdf.h - pdf.b_margin:
        pdf.add_page()


def _titre_page(pdf: FPDF, titre: str, sous_titre: str | None = None):
    pdf.police("serif", "", 24)
    pdf.set_text_color(*INK)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 11, titre, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if sous_titre:
        pdf.police("sans", "", 9.5)
        pdf.set_text_color(*TEXTE_2)
        pdf.multi_cell(_largeur(pdf), 5, sous_titre, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*INK)
    pdf.ln(1.5)


def _ensemble(pdf: FPDF, dessiner):
    """Dessine `dessiner(pdf)` d'un seul tenant : s'il ne tient pas dans la fin de la page,
    il commence sur la suivante (rendu d'essai `offset_rendering`, rien n'est dessiné deux
    fois). Un ensemble plus haut qu'une page se coupe normalement."""
    with pdf.offset_rendering() as essai:
        dessiner(essai)
    if essai.page_break_triggered and pdf.get_y() > pdf.t_margin + 30:
        pdf.add_page()
    dessiner(pdf)


def _section(pdf: FPDF, titre: str, compte: str | None = None):
    _place(pdf, 22)
    pdf.ln(1.5)
    pdf.set_x(pdf.l_margin)
    pdf.police("serif", "", 15)
    pdf.set_text_color(*INK)
    largeur = pdf.get_string_width(titre) + 2
    pdf.cell(largeur, 7, titre)
    if compte:
        pdf.police("sans", "", 8.5)
        pdf.set_text_color(*TEXTE_2)
        pdf.cell(0, 7, compte)
    pdf.ln(7.5)
    pdf.set_text_color(*INK)
    pdf.police("sans", "", 9.5)


def _para(pdf: FPDF, text: str, taille: float = 9.5, style: str = "", couleur=INK, h: float = 4.8):
    pdf.set_x(pdf.l_margin)
    pdf.police("sans", style, taille)
    pdf.set_text_color(*couleur)
    pdf.multi_cell(_largeur(pdf), h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*INK)


def _puce(pdf: FPDF, texte: str, couleur=INK, taille: float = 9.5):
    """Une ligne précédée d'une pastille de couleur (vert : geste gratuit)."""
    _place(pdf, 10)
    y = pdf.get_y()
    pdf.set_fill_color(*couleur)
    pdf.ellipse(pdf.l_margin + 0.6, y + 1.6, 1.8, 1.8, style="F")
    pdf.set_xy(pdf.l_margin + 4.5, y)
    pdf.police("sans", "", taille)
    pdf.multi_cell(_largeur(pdf) - 4.5, 4.5, texte, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(0.4)


def _hauteur_texte(pdf: FPDF, largeur: float, texte: str, h: float) -> float:
    lignes = pdf.multi_cell(largeur, h, texte, dry_run=True, output=MethodReturnValue.LINES)
    return len(lignes) * h


def _encadre(pdf: FPDF, blocs: list[tuple[str, str, float, str, tuple]], fond=SABLE, filet=None,
             padding: float = 4):
    """Encadré mesuré avant d'être dessiné. `blocs` : (role, style, taille, texte, couleur)."""
    largeur = _largeur(pdf) - 2 * padding
    hauteurs = []
    for role, style, taille, texte, _ in blocs:
        pdf.police(role, style, taille)
        hauteurs.append(_hauteur_texte(pdf, largeur, texte, taille * 0.5))
    total = sum(hauteurs) + 2 * padding + 1.2 * (len(blocs) - 1)
    _place(pdf, total + 2)
    x, y = pdf.l_margin, pdf.get_y()
    pdf.set_fill_color(*fond)
    if filet:
        pdf.set_draw_color(*filet)
        pdf.set_line_width(0.6)
        pdf.rect(x, y, _largeur(pdf), total, style="DF", round_corners=True, corner_radius=2)
    else:
        pdf.rect(x, y, _largeur(pdf), total, style="F", round_corners=True, corner_radius=2)
    pdf.set_y(y + padding)
    for (role, style, taille, texte, couleur), _h in zip(blocs, hauteurs):
        pdf.set_x(x + padding)
        pdf.police(role, style, taille)
        pdf.set_text_color(*couleur)
        pdf.multi_cell(largeur, taille * 0.5, texte, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.2)
    pdf.set_y(y + total + 2)
    pdf.set_text_color(*INK)
    pdf.set_line_width(0.2)


def _tableau(pdf: FPDF, entetes: list[str], largeurs: list[float], lignes: list[list[str]],
             aligns: list[str] | None = None):
    """Tableau fpdf2 : cellules sur plusieurs lignes, en-tête répété après un saut de page.

    Le texte entre `__` est en italique (deuxième ligne d'une cellule : contexte, occasion).
    """
    _place(pdf, 22)
    pdf.police("sans", "", 8)
    pdf.set_text_color(*INK)
    pdf.set_draw_color(*BORD)
    pdf.set_fill_color(*BLANC)
    pdf.set_line_width(0.25)
    entete = FontFace(emphasis="BOLD", color=INK, fill_color=SABLE, size_pt=7.5)
    with pdf.table(col_widths=largeurs, width=_largeur(pdf), text_align=aligns or "LEFT",
                   headings_style=entete, line_height=4, padding=(1.1, 1.3), markdown=True,
                   cell_fill_mode="NONE", borders_layout="HORIZONTAL_LINES", repeat_headings=1,
                   v_align="TOP") as table:
        ligne = table.row()
        for e in entetes:
            ligne.cell(e)
        for valeurs in lignes:
            ligne = table.row()
            for v in valeurs:
                ligne.cell(v)
    pdf.ln(2)


# --- Tableaux d'actions ---------------------------------------------------------------------

_ENTETES = ["Action", "Coût", "Aide MaPrimeRénov'", "Reste à charge", "Économie / an", "Retour"]
_LARGEURS = [59, 25, 29, 25, 23, 19]
_ALIGNS = ["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]


def _md(texte: str) -> str:
    """Neutralise les marqueurs markdown de fpdf2 dans un texte venu du moteur."""
    return texte.replace("**", "*").replace("__", "_").replace("--", "–")


def _ligne_action(a: dict, avec_occasion: bool) -> list[str]:
    action = _md(a["label"])
    complement = a.get("contexte") or (a.get("libelle_occasion") if avec_occasion else None)
    if complement:
        action += f"\n__{_md(complement[0].upper() + complement[1:])}__"
    cout = _plage(a["cout_eur"])
    if a.get("base_cout") == "surcout":
        cout = f"Surcoût\n{cout}"
    eco = a.get("economie_annuelle_eur") or {}
    economie = _eur(eco["central"]) if eco.get("central") is not None else "–"
    if a.get("categorie") == "eau_chaude":
        economie += "\n(eau chaude)"
    retour = _retour(a) + (" *" if _retour_trop_long(a) else "")
    return [action, cout, _plage_aide(a["aide_estimee_eur"]), _montant(a["reste_a_charge_eur"]), economie, retour]


def _table_actions(pdf: FPDF, actions: list[dict], avec_occasion: bool = False):
    _tableau(pdf, _ENTETES, _LARGEURS, [_ligne_action(a, avec_occasion) for a in actions], _ALIGNS)
    _explications(pdf, actions)


# v2.4 : ce que chaque action explique, en lignes courtes, après son tableau. Les textes
# viennent des fiches kb/action_* (via le moteur) : le PDF ne fait que les poser.
_EXPLICATIONS = (("pourquoi", "Pourquoi"), ("benefices", "Ce que ça apporte"),
                 ("vigilance", "À surveiller"), ("devis", "Sur le devis"))
_EXPLICATIONS_OCCASION = ("pourquoi", "benefices")


def _lignes_explication(a: dict) -> list[str]:
    cles = _EXPLICATIONS_OCCASION if a.get("horizon") == "a_l_occasion" else [c for c, _ in _EXPLICATIONS]
    lignes = []
    for cle, libelle in _EXPLICATIONS:
        valeur = a.get(cle)
        if cle not in cles or not valeur:
            continue
        texte = valeur if isinstance(valeur, str) else " · ".join(valeur)
        lignes.append(f"**{libelle} :** {_md(texte)}")
    return lignes


def _explications(pdf: FPDF, actions: list[dict]):
    for a in actions:
        lignes = _lignes_explication(a)
        if not lignes:
            continue

        def bloc(pdf, a=a, lignes=lignes):
            pdf.set_x(pdf.l_margin)
            pdf.police("sans", "B", 8.8)
            pdf.set_text_color(*INK)
            pdf.multi_cell(_largeur(pdf), 4.3, a["label"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.police("sans", "", 8.3)
            pdf.set_text_color(*TEXTE_2)
            for ligne in lignes:
                pdf.set_x(pdf.l_margin + 3)
                pdf.multi_cell(_largeur(pdf) - 3, 3.9, ligne, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*INK)
            pdf.ln(1.6)

        _ensemble(pdf, bloc)


def _aide_nulle(a: dict) -> bool:
    aide = a.get("aide_estimee_eur")
    return aide == 0 or (isinstance(aide, dict) and not aide["bas"] and not aide["haut"])


def _enumerer(mots: list[str]) -> str:
    return mots[0] if len(mots) == 1 else f"{', '.join(mots[:-1])} et {mots[-1]}"


def _note_commune(actions: list[dict]) -> tuple[str | None, list[dict]]:
    """Une seule phrase pour tous les travaux sortis de MaPrimeRénov' par geste.

    Le moteur pose une note par action ; sous trois tableaux, la même phrase revenait trois
    fois. On regroupe à l'affichage les actions SANS aide dont le geste est sorti du parcours
    (`ref.SORTIE_PAR_GESTE`), et on ne cite que les travaux présents. Les autres notes (PAC,
    régulation) restent une par une.
    """
    sortis = [a for a in actions if a.get("action") in ref.SORTIE_PAR_GESTE and _aide_nulle(a)]
    autres = [a for a in actions if a not in sortis and a.get("aide_note")]
    if not sortis:
        return None, autres
    presentes = {a["action"] for a in sortis}
    par_date: dict[str, list[str]] = {}
    for action, (nom, quand) in ref.SORTIE_PAR_GESTE.items():  # ordre fixe de la table
        if action in presentes:
            par_date.setdefault(quand, []).append(nom)
    dates = sorted(par_date, key=lambda d: d[6:] + d[3:5] + d[:2])
    detail = " ; ".join(f"{_enumerer(par_date[d])} depuis le {d}" for d in dates)
    phrase = (f"MaPrimeRénov' par geste ne finance plus ces travaux ({detail}). Primes CEE possibles, "
              "montant variable selon l'organisme")
    if any(a["action"] in ref.POSTES_ISOLATION for a in sortis):
        phrase += " ; l'isolation reste finançable en rénovation d'ampleur"
    return phrase + ".", autres


def _notes_aides(pdf: FPDF, audit: dict, actions: list[dict]):
    """Notes d'aide : la phrase commune, puis les notes propres, puis la légende « > 30 ans »."""
    commune, autres = _note_commune(actions)
    lignes = [f"Aides MaPrimeRénov' du revenu le plus élevé au plus modeste, barèmes relevés le "
              f"{_date_aides(audit)}, à vérifier au moment du dépôt."]
    if commune:
        lignes.append(commune)
    notes: dict[str, list[str]] = {}
    for a in autres:
        notes.setdefault(a["aide_note"], []).append(a["label"])
    lignes += [f"{', '.join(labels)} : {note}." for note, labels in notes.items()]
    if any(_retour_trop_long(a) for a in actions):
        lignes.append("* " + _LEGENDE_RETOUR.format(max=settings.audit_retour_affichage_max_ans))
    pdf.police("sans", "", 7)
    _place(pdf, sum(_hauteur_texte(pdf, _largeur(pdf), ligne, 3.3) + 0.5 for ligne in lignes))
    for ligne in lignes:
        _para(pdf, ligne, taille=7, couleur=TEXTE_2, h=3.3)
        pdf.ln(0.5)


# --- v2.3 : page 1, « Votre maison en bref » -------------------------------------------------

def _entrees(audit: dict) -> dict:
    return {e["champ"]: e for e in audit.get("entrees", [])}


def _valeur(entrees: dict, champ: str, defaut=None):
    e = entrees.get(champ)
    if e and e.get("valeur") is not None:
        return e["valeur"], False
    return defaut, True


def _lignes_maison(audit: dict) -> list[tuple[str, str]]:
    """Ce que la fiche dit de la maison, en clair ; une valeur supposée le dit."""
    e = _entrees(audit)
    c = audit.get("consommation", {})
    sup = " (supposé)"
    lignes = []

    type_l, _ = _valeur(e, "type_logement", "logement")
    surface, s_sup = _valeur(e, "surface_habitable")
    niveaux, n_sup = _valeur(e, "nb_niveaux", 1)
    morceaux = [_libelle("type_logement", type_l).capitalize()]
    morceaux.append(f"{_milliers(surface)}{NBSP}m²" if surface else "surface inconnue")
    morceaux.append(f"{niveaux} niveau{'x' if niveaux > 1 else ''}" + (sup if n_sup else ""))
    lignes.append(("Logement", " · ".join(morceaux)))

    cp, _ = _valeur(e, "code_postal", "code postal inconnu")
    zone = c.get("zone_climatique")
    lignes.append(("Situation", f"{cp} · zone {zone} ({_libelle('zone_climatique', zone)})" if zone else str(cp)))

    chauffage, ch_sup = _valeur(e, "chauffage_principal", ref.CHAUFFAGE_DEFAUT)
    annee, _ = _valeur(e, "chauffage_principal_annee")
    texte = _libelle("chauffage_principal", chauffage).capitalize() + (sup if ch_sup else "")
    if annee:
        texte += f", de {annee}"
    appoint, _ = _valeur(e, "chauffage_appoint")
    if appoint:
        texte += f" ; appoint : {_libelle('chauffage_appoint', appoint)}"
    lignes.append(("Chauffage", texte))

    ecs, ecs_sup = _valeur(e, "ecs", settings.audit_ecs_defaut)
    ecs_annee, _ = _valeur(e, "ecs_annee")
    texte = _libelle("ecs", ecs).capitalize() + (sup if ecs_sup else "")
    if ecs_annee:
        texte += f", de {ecs_annee}"
    lignes.append(("Eau chaude", texte))

    elec, elec_sup = _valeur(e, "conso_elec_kwh_an")
    lignes.append(("Électricité", f"{_kwh(elec)} par an, d'après votre facture" if not elec_sup
                   else "consommation non déclarée"))
    return lignes


def _echelle_dpe(pdf: FPDF, x: float, y: float, lettre: str):
    """Sept bandes de longueur croissante ; la lettre DÉCLARÉE est cerclée. Jamais estimée."""
    h, ecart, base, pas = 5.2, 1.2, 16, 5.5
    for i, l in enumerate("ABCDEFG"):
        yy = y + i * (h + ecart)
        w = base + i * pas
        pdf.set_fill_color(*DPE_COULEURS[l])
        pdf.rect(x, yy, w, h, style="F")
        pdf.police("sans", "B", 8.5)
        pdf.set_text_color(*(INK if l in DPE_LETTRE_ENCRE else BLANC))
        pdf.set_xy(x + 1.5, yy)
        pdf.cell(6, h, l)
        if l == lettre:
            pdf.set_draw_color(*INK)
            pdf.set_line_width(0.7)
            pdf.rect(x - 0.8, yy - 0.8, w + 1.6, h + 1.6, style="D")
            pdf.set_xy(x + w + 2.5, yy)
            pdf.police("sans", "B", 8.5)
            pdf.set_text_color(*INK)
            pdf.cell(30, h, "votre lettre")
    pdf.set_text_color(*INK)
    pdf.set_line_width(0.2)
    return y + 7 * (h + ecart)


def _taille_valeur(valeur: str) -> float:
    return 10 if len(valeur) > 32 else 11.5


def _carte(pdf: FPDF, x: float, y: float, w: float, h: float, titre: str, valeur: str, note: str,
           accent: bool = False):
    pdf.set_fill_color(*BLANC)
    pdf.set_draw_color(*(ACCENT if accent else BORD))
    pdf.set_line_width(0.5 if accent else 0.3)
    pdf.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=2)
    pdf.set_xy(x + 3.5, y + 3)
    pdf.police("sans", "B", 7.5)
    pdf.set_text_color(*(ACCENT if accent else TEXTE_2))
    pdf.cell(w - 7, 4, titre.upper())
    pdf.set_xy(x + 3.5, y + 8.5)
    taille = _taille_valeur(valeur)
    pdf.police("sans", "B", taille)
    pdf.set_text_color(*INK)
    pdf.multi_cell(w - 7, taille * 0.47, valeur)
    pdf.set_x(x + 3.5)
    pdf.police("sans", "", 8)
    pdf.set_text_color(*TEXTE_2)
    pdf.multi_cell(w - 7, 3.9, note)
    pdf.set_text_color(*INK)
    pdf.set_line_width(0.2)


def _cartes(pdf: FPDF, audit: dict):
    sy, c = audit["synthese"], audit["consommation"]
    plan = sy["plan_recommande"]
    energie = _ENERGIE.get(c.get("energie_chauffage"), c.get("energie_chauffage"))
    facture = c.get("base_economies") == "declaree"
    note = f"{energie.capitalize()}, " + ("d'après votre facture" if facture else "estimé (pas de relevé)")
    eau = (audit.get("couts") or {}).get("eau_chaude_eur_an")
    if eau:  # v2.4
        note += f", et environ {_eur(round(eau, -1))} par an pour l'eau chaude"
    cartes = [("Votre chauffage", f"{_eur(c['cout_chauffage_actuel_eur'])} par an", note)]
    if plan["nb"]:
        cartes.append(("Le plan recommandé", f"{_plage_txt(plan['economie_annuelle_eur'])} par an",
                       f"d'économie, pour {_plage_txt(plan['reste_a_charge_eur'])} de reste à charge"))
    else:
        cartes.append(("Le plan recommandé", "Pas de travaux rentables à court terme",
                       "Commencez par les gestes gratuits de votre plan"))
    cartes.append(("Votre plan", sy.get("decompte", ""), "le détail est page suivante"))

    w, gout = (_largeur(pdf) - 2 * 4) / 3, 4
    hauteurs = []
    for _, v, _ in cartes:
        pdf.police("sans", "B", _taille_valeur(v))
        hauteurs.append(_hauteur_texte(pdf, w - 7, v, _taille_valeur(v) * 0.47))
    hauteur = 10 + max(hauteurs)
    pdf.police("sans", "", 8)
    hauteur += max(_hauteur_texte(pdf, w - 7, n, 3.9) for _, _, n in cartes) + 3.5
    _place(pdf, hauteur + 4)
    y = pdf.get_y()
    for i, (titre, valeur, note) in enumerate(cartes):
        _carte(pdf, pdf.l_margin + i * (w + gout), y, w, hauteur, titre, valeur, note, accent=(i == 1))
    pdf.set_y(y + hauteur + 5)


def _premiere_etape(pdf: FPDF, audit: dict):
    sy = audit["synthese"]
    blocs = [("sans", "B", 8, "VOTRE PREMIÈRE ÉTAPE", ACCENT)]
    action = None
    if sy.get("premiere_action_type") == "action":
        action = next((a for a in audit.get("priorites", []) if a["label"] == sy.get("premiere_action")
                       and a.get("horizon") in ("maintenant", "prioritaire")), None)
    blocs.append(("serif", "", 16, sy.get("premiere_action") or "", INK))
    if action:
        if action.get("pourquoi"):  # v2.4 : la raison, qui dit déjà le contexte
            blocs.append(("sans", "", 9.5, action["pourquoi"], TEXTE_2))
        elif action.get("contexte"):
            blocs.append(("sans", "", 9.5, action["contexte"][0].upper() + action["contexte"][1:] + ".", TEXTE_2))
        cout = ("Surcoût" if action.get("base_cout") == "surcout" else "Coût") + f" : {_plage_txt(action['cout_eur'])}"
        aide = action["aide_estimee_eur"]
        if isinstance(aide, dict) and (aide["bas"] or aide["haut"]):
            cout += f", aide {_plage_txt(aide)} selon vos revenus"
        eco = action["economie_annuelle_eur"]
        chiffres = f"{cout} · économie {_plage_txt(eco)} par an"
        if action.get("temps_retour_ans") is not None:
            chiffres += f" · retour {_retour(action)}"
        blocs.append(("sans", "B", 9.5, chiffres, INK))
    _encadre(pdf, blocs, fond=BLANC, filet=ACCENT, padding=4.5)


def _a_preciser(pdf: FPDF, audit: dict):
    items = audit.get("a_preciser") or []
    if not items:
        return
    _section(pdf, "Pour un pré-audit plus précis")
    for it in items:
        _puce(pdf, f"{it['libelle']} — {it['hypothese']}.", couleur=TEXTE_2, taille=9)
    _para(pdf, "À compléter dans votre fiche Maison : le prochain pré-audit en tiendra compte.",
          taille=8.5, couleur=TEXTE_2)


def _page_en_bref(pdf: FPDF, audit: dict, house_label: str | None):
    score = audit.get("completeness_score")
    entete = date.today().strftime("%d/%m/%Y") + (f" · {house_label}" if house_label else "")
    phrase = (f"Établi à partir de votre fiche Maison, complétée à {_pct(score)} : une partie des chiffres "
              "repose sur des hypothèses (voir la dernière page).")
    _titre_page(pdf, "Votre maison en bref", f"{entete}\n{phrase}")

    # Deux colonnes : la maison à gauche, l'échelle DPE à droite.
    y0 = pdf.get_y()
    gauche = 112
    for cle, valeur in _lignes_maison(audit):
        pdf.set_x(pdf.l_margin)
        pdf.police("sans", "", 8)
        pdf.set_text_color(*TEXTE_2)
        pdf.cell(24, 5.4, cle.upper())
        pdf.police("sans", "", 9.5)
        pdf.set_text_color(*INK)
        pdf.multi_cell(gauche - 24, 5.4, valeur, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(0.6)
    y_gauche = pdf.get_y()

    x_dpe = pdf.l_margin + gauche + 6
    lettre, sup = _valeur(_entrees(audit), "dpe_lettre")
    lettre = (lettre or "").upper()
    if not sup and lettre in DPE_COULEURS:
        y_fin = _echelle_dpe(pdf, x_dpe, y0, lettre)
        pdf.set_xy(x_dpe, y_fin + 1)
        pdf.police("sans", "", 7.5)
        pdf.set_text_color(*TEXTE_2)
        pdf.multi_cell(_largeur(pdf) - gauche - 6, 3.6,
                       "Lettre déclarée dans votre fiche. Le pré-audit ne recalcule pas votre DPE.")
    else:
        pdf.set_xy(x_dpe, y0)
        pdf.police("sans", "B", 8)
        pdf.set_text_color(*TEXTE_2)
        pdf.cell(0, 5, "DPE")
        pdf.set_xy(x_dpe, y0 + 6)
        pdf.police("sans", "", 8.5)
        pdf.multi_cell(_largeur(pdf) - gauche - 6, 4.3,
                       _ORIGINE_PHRASE.get(audit.get("consommation", {}).get("origine"), ""))
    pdf.set_text_color(*INK)
    pdf.set_y(max(y_gauche, pdf.get_y()) + 5)

    _cartes(pdf, audit)
    _premiere_etape(pdf, audit)
    _a_preciser(pdf, audit)


# --- v2.3 : page 2, « Votre plan » ------------------------------------------------------------

def _frise(pdf: FPDF, etapes: list[tuple[str, int]]):
    """Quatre étapes reliées ; une étape vide est grisée."""
    _place(pdf, 24)
    y = pdf.get_y() + 1
    pas = _largeur(pdf) / len(etapes)
    centres = [pdf.l_margin + pas * (i + 0.5) for i in range(len(etapes))]
    pdf.set_draw_color(*BORD)
    pdf.set_line_width(0.6)
    pdf.line(centres[0], y, centres[-1], y)
    for (libelle, n), cx in zip(etapes, centres):
        vide = n == 0
        pdf.set_fill_color(*(BORD if vide else ACCENT))
        pdf.ellipse(cx - 4.5, y - 4.5, 9, 9, style="F")
        pdf.police("sans", "B", 9.5)
        pdf.set_text_color(*(TEXTE_2 if vide else BLANC))
        pdf.set_xy(cx - 4.5, y - 4.5)
        pdf.cell(9, 9, str(n), align="C")
        pdf.police("sans", "B" if not vide else "", 8.5)
        pdf.set_text_color(*(TEXTE_2 if vide else INK))
        pdf.set_xy(cx - pas / 2, y + 6)
        pdf.cell(pas, 4.5, libelle, align="C")
    pdf.set_text_color(*INK)
    pdf.set_line_width(0.2)
    pdf.set_y(y + 12)


def _solaire(pdf: FPDF, sol: dict):
    if sol["type"] == "piste":
        _para(pdf, sol["texte"])
        return
    e = sol["etude"]
    kwc = f"{_dec(float(e['puissance_kwc']))}{NBSP}kWc" if e.get("puissance_kwc") is not None else "–"
    lignes = [f"Installation étudiée : {kwc}" + (f" ({e['option']})" if e.get("option") else "")]
    if e.get("investissement_eur") is not None:
        lignes.append(f"Investissement : {_eur(e['investissement_eur'])}")
    if e.get("economie_1re_annee_eur") is not None:
        lignes.append(f"Économie la première année : {_eur(e['economie_1re_annee_eur'])}")
    if e.get("temps_retour_ans") is not None:
        lignes.append(f"Temps de retour : {_dec(float(e['temps_retour_ans']))}{NBSP}ans")
    if e.get("gain_net_25_ans_eur") is not None:
        lignes.append(f"Gain net sur 25 ans : {_eur(e['gain_net_25_ans_eur'])}")
    if e.get("autonomie_pct") is not None:
        lignes.append(f"Autonomie : {_pct(e['autonomie_pct'])}")
    for ligne in lignes:
        _puce(pdf, ligne, couleur=TEXTE_2)
    _para(pdf, f"Source : {sol['source']}." + (f" {sol['mention'].capitalize()}." if sol.get("mention") else ""),
          taille=8.5, couleur=TEXTE_2)


def _ampleur(pdf: FPDF, amp: dict):
    """La piste de la rénovation d'ampleur, sans chiffre (kb/renovation_ampleur.md)."""
    if amp.get("texte"):
        pdf.ln(0.8)
        _para(pdf, amp["texte"])
    if amp.get("fossile"):
        _para(pdf, amp["fossile"], style="B", taille=9)
    if amp.get("vigilance"):
        pdf.set_x(pdf.l_margin)
        pdf.police("sans", "", 8.3)
        pdf.set_text_color(*TEXTE_2)
        pdf.multi_cell(_largeur(pdf), 3.9, f"**À surveiller :** {_md(' · '.join(amp['vigilance']))}",
                       markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*INK)
    pdf.ln(1)


def _intertitre(pdf: FPDF, titre: str):
    _place(pdf, 14)
    pdf.ln(0.8)
    _para(pdf, titre, taille=9.5, style="B", h=5)


def _compte(n: int, mot: str = "élément") -> str:
    return f"{n} {mot}{'s' if n > 1 else ''}"


def _page_plan(pdf: FPDF, audit: dict):
    sy = audit["synthese"]
    travaux = [a for a in audit.get("priorites", []) if a.get("categorie") != "production"]
    par = {h: [a for a in travaux if a.get("horizon") == h] for h in ref.HORIZONS}
    gestes, conseils, sol = audit.get("gestes", []), audit.get("conseils_equipements", []), audit.get("solaire")
    contrat, dpe, ampleur = audit.get("contrat") or [], audit.get("dpe_attestation"), audit.get("renovation_ampleur")
    n_maintenant = len(gestes) + len(conseils) + len(par["maintenant"]) + len(contrat) + (1 if dpe else 0)
    n_loin = (1 if sol else 0) + (1 if ampleur else 0)

    _titre_page(pdf, "Votre plan")
    _frise(pdf, [("Maintenant", n_maintenant), ("Cette année", len(par["prioritaire"])),
                 ("À l'occasion de…", len(par["a_l_occasion"])), ("Pour aller plus loin", n_loin)])

    _section(pdf, "Maintenant", _compte(n_maintenant))
    for g in gestes:
        _puce(pdf, g["texte"], couleur=VERT)
    for c in conseils:
        _puce(pdf, c["texte"], couleur=ACCENT)
    if dpe:
        _puce(pdf, dpe["texte"], couleur=ACCENT)
    if contrat:
        _intertitre(pdf, "Votre contrat")
        for levier in contrat:
            _puce(pdf, levier["texte"], couleur=VERT)
    if par["maintenant"]:
        _table_actions(pdf, par["maintenant"])

    _section(pdf, "Cette année", _compte(len(par["prioritaire"]), "action"))
    if par["prioritaire"]:
        _table_actions(pdf, par["prioritaire"])
    else:
        _para(pdf, "Aucun investissement ne se justifie à court terme : les gestes ci-dessus suffisent pour l'instant.")

    def occasion(pdf):
        _section(pdf, "À l'occasion de…", _compte(len(par["a_l_occasion"]), "action"))
        if par["a_l_occasion"]:
            if sy.get("message_sans_isolation"):
                _para(pdf, sy["message_sans_isolation"], taille=9)
                pdf.ln(1)
            _table_actions(pdf, par["a_l_occasion"], avec_occasion=True)
        else:
            _para(pdf, "Rien à prévoir pour l'instant.")

    def fin(pdf):
        pdf.ln(1)
        _en_resume(pdf, sy)
        _notes_aides(pdf, audit, travaux)

    # v2.5 : « À l'occasion de… » peut se couper après son tableau (chaque explication reste
    # entière) ; « En résumé » et la note d'aide commune restent ensemble, sans jamais se
    # couper. Les tenir avec tout le bloc laissait une demi-page vide.
    occasion(pdf)
    if sol or ampleur:
        _section(pdf, "Pour aller plus loin")
    if sol:
        _solaire(pdf, sol)
    if ampleur:
        _ampleur(pdf, ampleur)
    _ensemble(pdf, fin)


def _phrase_bloc(bloc: dict) -> str:
    morceaux = [f"coût {_plage_txt(bloc['investissement_eur'])}"]
    aides = bloc["aides_estimees_eur"]
    morceaux.append(f"aides {_plage_txt(aides)} selon vos revenus" if aides["bas"] or aides["haut"]
                    else "aucune aide MaPrimeRénov'")
    morceaux.append(f"reste à charge {_plage_txt(bloc['reste_a_charge_eur'])}")
    morceaux.append(f"économie {_plage_txt(bloc['economie_annuelle_eur'])} par an")
    return ", ".join(morceaux)


def _en_resume(pdf: FPDF, sy: dict):
    plan, occ = sy["plan_recommande"], sy["a_l_occasion"]
    blocs = [("serif", "", 15, "En résumé", INK)]
    if plan["nb"]:
        blocs.append(("sans", "B", 9.5, f"Le plan recommandé ({_compte(plan['nb'], 'action')}) : "
                                        f"{_phrase_bloc(plan)}.", INK))
    else:
        blocs.append(("sans", "B", 9.5, "Pas de travaux rentables à court terme : les gestes gratuits sont "
                                        "votre plan pour l'instant.", INK))
    if occ["nb"]:
        blocs.append(("sans", "", 9, f"Si vous faites aussi les travaux à prévoir à l'occasion "
                                     f"({_compte(occ['nb'], 'action')}) : {_phrase_bloc(occ)}.", TEXTE_2))
    _encadre(pdf, blocs, padding=3.2)


# --- v2.3 : page 3, « Comprendre votre maison » ----------------------------------------------

def _deperditions(pdf: FPDF, audit: dict):
    pmax = max((d["part_pct"] for d in audit.get("deperditions", [])), default=1) or 1
    for d in audit.get("deperditions", []):
        _place(pdf, 7)
        y = pdf.get_y()
        pdf.set_x(pdf.l_margin)
        pdf.police("sans", "", 9.5)
        pdf.cell(45, 6, _POSTE_LABEL.get(d["poste"], d["poste"]))
        pdf.set_fill_color(*SABLE)
        pdf.rect(pdf.l_margin + 45, y + 1.3, 110, 3.4, style="F")
        pdf.set_fill_color(*ACCENT)
        pdf.rect(pdf.l_margin + 45, y + 1.3, max(0.8, 110 * d["part_pct"] / pmax), 3.4, style="F")
        pdf.set_xy(pdf.l_margin + 158, y)
        pdf.cell(_largeur(pdf) - 158, 6, _pct(d["part_pct"]), align="R")
        pdf.ln(6.4)


def _consommation_v2(pdf: FPDF, audit: dict, encadre: bool = False):
    c = audit["consommation"]
    _para(pdf,
          f"Consommation de chauffage estimée : {_kwh(c['conso_chauffage_estimee_kwh_an'])} par an de "
          f"{_ENERGIE.get(c.get('energie_chauffage'), c.get('energie_chauffage'))} "
          f"({_ORIGINE.get(c.get('origine'), c.get('origine'))}, zone climatique {c.get('zone_climatique')}).")
    if c.get("conso_chauffage_declaree_kwh_an") is not None:
        _para(pdf,
              f"D'après votre facture : {_kwh(c['conso_elec_declaree_kwh_an'])} d'électricité par an, dont "
              f"environ {_kwh(c['usages_specifiques_kwh_an'])} pour les usages courants (appareils, eau "
              f"chaude) : il reste {_kwh(c['conso_chauffage_declaree_kwh_an'])} pour le chauffage.")
    pdf.ln(1.5)
    if c.get("message_ratio"):
        if encadre:
            _encadre(pdf, [("sans", "B", 8, "VOTRE FACTURE ET LA THÉORIE", ACCENT),
                           ("sans", "", 9.5, c["message_ratio"], INK)])
        else:
            _para(pdf, c["message_ratio"])
    for alerte in audit.get("alertes", []):
        _para(pdf, f"Attention : {alerte}", style="B")
    _para(pdf,
          f"Les économies portent sur {_kwh(c['conso_chauffage_retenue_kwh_an'])} de chauffage par an, au prix "
          f"de {_dec(c['prix_energie_eur_kwh'], 4)}{NBSP}€/kWh, soit environ "
          f"{_eur(c['cout_chauffage_actuel_eur'])} par an.")


def _dans_le_temps(pdf: FPDF, audit: dict):
    """v2.4 : le coût sur 10 ans et les émissions, une ligne chacun, sans pictogramme."""
    co, cl = audit.get("couts"), audit.get("climat")
    if co:
        quoi = ("votre chauffage et votre eau chaude vous coûteraient" if co.get("eau_chaude_eur_an")
                else "votre chauffage vous coûterait")
        hausse = _dec(float(co["hausse_pct_an"])).removesuffix(",0")
        phrase = f"Sur 10 ans, à +{hausse}{NBSP}%/an, {quoi} environ {_eur(co['chauffage_et_eau_chaude_10_ans_eur'])}"
        if co.get("economie_10_ans_plan_recommande_eur"):
            phrase += f" ; le plan recommandé en économiserait environ {_eur(co['economie_10_ans_plan_recommande_eur'])}"
        pdf.ln(1)
        _para(pdf, phrase + ".")
    if cl:
        aujourd_hui = cl["chauffage_kg_an"] + (cl.get("eau_chaude_kg_an") or 0)
        _para(pdf, f"Émissions de CO₂ : environ {_milliers(aujourd_hui)}{NBSP}kg/an aujourd'hui, "
                   f"{_milliers(cl['apres_plan_recommande_kg_an'])}{NBSP}kg/an après le plan recommandé.")


def _puissance(pdf: FPDF, bloc: dict):
    """v2.6 : les phrases de la fiche PAC, telles que le moteur les a remplies. Air/eau : la
    plage et les radiateurs pièce par pièce ; air/air : la seule phrase de puissance."""
    _section(pdf, "Puissance de chauffage")
    _para(pdf, bloc["texte"])
    if bloc.get("texte_plage"):
        pdf.ln(1)
        _para(pdf, bloc["texte_plage"])
    lignes = [r["texte"] for r in bloc.get("radiateurs") or [] if r.get("texte")]
    if lignes or bloc.get("note_radiateurs"):
        pdf.ln(1)
    for texte in lignes:
        _puce(pdf, texte)
    if bloc.get("note_radiateurs"):
        _para(pdf, bloc["note_radiateurs"], taille=9, couleur=TEXTE_2)


def _confort_ete(pdf: FPDF, ete: dict, titre: str):
    _section(pdf, titre)
    for conseil in ete["conseils"]:
        _puce(pdf, conseil, couleur=VERT)
    if ete.get("note_clim"):
        _puce(pdf, ete["note_clim"], couleur=VERT)
    if ete.get("note_combles"):
        _para(pdf, ete["note_combles"], taille=9, couleur=TEXTE_2)


def _page_comprendre(pdf: FPDF, audit: dict):
    _titre_page(pdf, "Comprendre votre maison")
    _section(pdf, "Où part la chaleur")
    _deperditions(pdf, audit)
    phrase = ("Ces parts disent par où part la chaleur, pas ce que chaque poste vous coûte : le coût dépend de "
              "votre chauffage et de votre consommation réelle (ci-dessous).")
    if audit.get("deperditions_statut") == "suppose":
        phrase += " (Répartition supposée : une partie de l'isolation est inconnue.)"
    pdf.ln(1)
    _para(pdf, phrase, taille=8.5, couleur=TEXTE_2)
    _section(pdf, "Votre consommation")
    _consommation_v2(pdf, audit, encadre=True)
    _dans_le_temps(pdf, audit)
    if (audit.get("puissance") or {}).get("affichage"):
        _puissance(pdf, audit["puissance"])
    if audit.get("confort_ete"):
        _confort_ete(pdf, audit["confort_ete"], "Confort d'été")


# --- Dernière page, « Hypothèses et méthode » ------------------------------------------------

def _valeur_lisible(v) -> str:
    if isinstance(v, dict):
        return " ; ".join(f"{k} : {_valeur_lisible(x)}" for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return " / ".join(_valeur_lisible(x) for x in v)
    if isinstance(v, float):
        return _dec(v, None)
    return str(v)


_CLE_BRUTE = re.compile(r"[a-z]+_[a-z_]+")


def _terme(x) -> str:
    """Un mot technique des hypothèses, en français (action, poste, équipement, forme d'aide…)."""
    x = str(x)
    if x in ref.ACTIONS:
        return ref.ACTIONS[x]["label"]
    for table in (ref.TERMES_HYPOTHESES, ref.LIBELLE_VALEUR["chauffage_principal"], ref.LIBELLE_VALEUR["ecs"]):
        if x in table:
            return table[x]
    return x


def _valeur_fr(v) -> str:
    if isinstance(v, dict):
        return " ; ".join(f"{_terme(k)} {_valeur_fr(x)}" for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return " / ".join(_valeur_fr(x) for x in v)
    if isinstance(v, bool):
        return "oui" if v else "non"
    if isinstance(v, float):
        return _dec(v, None)
    if isinstance(v, int):
        return _milliers(v) if abs(v) >= 1000 else str(v)
    return _terme(v)


def _reference_lisible(h: dict) -> str | None:
    """« Consommation moyenne d'un DPE D : 215 kWh/m²/an … — source, date », ou None si la clé
    n'a pas de libellé ou si sa valeur garde un mot technique : elle part alors en annexe brute."""
    cle, _, param = h["cle"].partition("[")
    gabarit = ref.LIBELLES_HYPOTHESES.get(cle)
    if not gabarit:
        return None
    texte = gabarit.format(param=_terme(param.rstrip("]")), valeur=_valeur_fr(h["valeur"]))
    if _CLE_BRUTE.search(texte):
        return None
    date_src = f", {date.fromisoformat(h['date']).strftime('%d/%m/%Y')}" if h.get("date") else ""
    ligne = f"{texte} — {_source_lisible(h['source'])}{date_src}."
    return None if _CLE_BRUTE.search(ligne) else ligne


def _source_lisible(source: str) -> str:
    """La source telle qu'un lecteur la comprend : sans nom de fichier ni nom de réglage."""
    source = re.sub(r"kb/[\w.]+", "fiches Helios", source)
    return re.sub(r"\s*\([^)]*_[^)]*\)", "", source)


def _hypotheses_fiche(audit: dict) -> list[str]:
    lignes = [h["valeur"] for h in audit.get("hypotheses", [])
              if h.get("source") == "Fiche Maison" and isinstance(h.get("valeur"), str)]
    return [l[0].upper() + l[1:] for l in lignes]


def _page_hypotheses(pdf: FPDF, audit: dict):
    # Suit le contenu ; ne passe à la page suivante que si le titre et les premières lignes
    # ne tiennent pas.
    pdf.ln(6)
    if pdf.will_page_break(45):
        pdf.add_page()
    _titre_page(pdf, "Hypothèses et méthode")

    supposes = champs_supposes(audit.get("entrees", []))
    if supposes:
        _section(pdf, "Ce que nous avons supposé")
        for it in supposes:
            _puce(pdf, f"{it['libelle']} — {it['hypothese']}.", couleur=TEXTE_2, taille=9)
    fiche = _hypotheses_fiche(audit)
    if fiche:
        _section(pdf, "Hypothèses tirées de votre fiche")
        for ligne in fiche:
            _puce(pdf, ligne, couleur=TEXTE_2, taille=9)

    refs = [h for h in audit.get("hypotheses", []) if h.get("source") != "Fiche Maison"]
    lisibles = [(h, _reference_lisible(h)) for h in refs]
    if refs:
        _section(pdf, "Valeurs de référence")
        for _, texte in lisibles:
            if texte:
                _para(pdf, texte, taille=7.5, couleur=TEXTE_2, h=3.6)
                pdf.ln(0.4)

    pdf.ln(3)
    _para(pdf, _STATUTS, taille=8, couleur=TEXTE_2)
    pdf.ln(1)
    _para(pdf, f"Version du moteur : {audit.get('version_helios', '')} · aides : relevé du {_date_aides(audit)}.",
          taille=8, couleur=TEXTE_2)
    pdf.ln(1)
    _para(pdf, audit.get("avertissement", ""), taille=8.5, style="B")

    brutes = [h for h, texte in lisibles if not texte]
    if brutes:
        _section(pdf, "Autres paramètres techniques")
        for h in brutes:
            _para(pdf, f"{h['cle']} : {_valeur_lisible(h['valeur'])} — {h['source']}.", taille=7,
                  couleur=TEXTE_2, h=3.3)


# --- Formats antérieurs (v1, v2, v2.1, v2.2) : leur structure, les règles d'aujourd'hui ------

def _entete_ancien(pdf: FPDF, audit: dict, house_label: str | None):
    _titre_page(pdf, "Votre pré-audit")
    niveau = _NIVEAU.get(audit.get("niveau"), audit.get("niveau"))
    lignes = [date.today().strftime("%d/%m/%Y") + (f" · {house_label}" if house_label else ""),
              f"Fiche complétée à {_pct(audit.get('completeness_score'))} · {niveau} · moteur "
              f"{audit.get('version_helios', '')}"]
    for l in lignes:
        _para(pdf, l, taille=9, couleur=TEXTE_2)


def _synthese_v1_v2(pdf: FPDF, sy: dict):
    _section(pdf, "En résumé")
    if sy.get("nb_actions"):
        aides = sy["aides_estimees_eur"]
        aides_txt = (f"{_plage_txt(aides)} selon vos revenus (barèmes à vérifier)"
                     if isinstance(aides, dict) else _eur(aides))
        _para(pdf, f"{sy['nb_actions']} actions recommandées. Investissement total estimé : "
                   f"{_plage_txt(sy['investissement_eur'])}, aides estimées : {aides_txt}.")
        if sy.get("economie_annuelle_totale_eur"):
            _para(pdf, f"Économie annuelle totale potentielle : {_plage_txt(sy['economie_annuelle_totale_eur'])}.")
        if sy.get("premiere_action"):
            _para(pdf, f"Première étape conseillée : {sy['premiere_action']}.")
    else:
        _para(pdf, "Aucune action prioritaire détectée : votre logement est déjà bien optimisé.")


def _priorites_anciennes(pdf: FPDF, audit: dict, v2: bool):
    priorites = audit.get("priorites", [])
    entetes = ["Action", "Coût", "Aide", "Reste à charge", "Économie / an", "Retour"] + (["Quand"] if v2 else [])
    largeurs = [50, 26, 22, 25, 22, 17] + ([18] if v2 else [])
    lignes = []
    for a in priorites:
        ligne = [f"{a['rang']}. {_md(a['label'])}", _plage(a["cout_eur"]), _plage_aide(a["aide_estimee_eur"]),
                 _montant(a["reste_a_charge_eur"]), _eur(a["economie_annuelle_eur"]["central"]),
                 _retour(a) + (" *" if _retour_trop_long(a) else "")]
        if v2:
            ligne.append(_HORIZON.get(a.get("horizon"), "–"))
        lignes.append(ligne)
    _tableau(pdf, entetes, largeurs, lignes, ["LEFT"] + ["RIGHT"] * (len(entetes) - 1))
    if any(_retour_trop_long(a) for a in priorites):
        _para(pdf, "* " + _LEGENDE_RETOUR.format(max=settings.audit_retour_affichage_max_ans),
              taille=7.8, couleur=TEXTE_2)
    occasion = [a for a in priorites if a.get("horizon") == "a_l_occasion"]
    if occasion:
        _para(pdf, "À faire à l'occasion, pas en priorité (le temps de retour seul ne le justifie pas) :", taille=9)
        for a in occasion:
            _puce(pdf, f"{a['label']} : {a.get('libelle_occasion') or 'lors de travaux sur ce poste'}.",
                  couleur=TEXTE_2, taille=9)


def _plan_v21(pdf: FPDF, audit: dict):
    sy = audit.get("synthese", {})
    travaux = [a for a in audit.get("priorites", []) if a.get("categorie") != "production"]
    par = {h: [a for a in travaux if a.get("horizon") == h] for h in ref.HORIZONS}

    _section(pdf, "Votre plan")
    _para(pdf, f"{sy.get('decompte', '')}. Première étape : {sy.get('premiere_action')}.")
    if sy.get("message_sans_isolation"):
        # Texte stocké avec l'ancien libellé : il reste tel quel, c'est la donnée de l'audit.
        _para(pdf, sy["message_sans_isolation"], taille=9)

    _section(pdf, "Maintenant")
    for g in audit.get("gestes", []):
        _puce(pdf, g["texte"], couleur=VERT)
    for c in audit.get("conseils_equipements", []):
        _puce(pdf, c["texte"], couleur=ACCENT)
    if par["maintenant"]:
        _table_actions(pdf, par["maintenant"])

    _section(pdf, "Cette année")
    if par["prioritaire"]:
        _table_actions(pdf, par["prioritaire"])
    else:
        _para(pdf, "Aucun investissement ne se justifie à court terme : les gestes ci-dessus suffisent pour l'instant.")

    _section(pdf, "À l'occasion de…")
    if par["a_l_occasion"]:
        _table_actions(pdf, par["a_l_occasion"], avec_occasion=True)
    else:
        _para(pdf, "Rien à prévoir pour l'instant.")
    _notes_aides(pdf, audit, travaux)

    if audit.get("solaire"):
        _section(pdf, "Pour aller plus loin")
        _solaire(pdf, audit["solaire"])
    if audit.get("confort_ete"):
        _confort_ete(pdf, audit["confort_ete"], "Confort d'été")


def _synthese_v21(pdf: FPDF, audit: dict):
    sy = audit.get("synthese", {})
    _section(pdf, "En résumé")
    _para(pdf, f"{sy.get('decompte', '')}.")
    if sy.get("nb_actions"):
        a, r = sy["aides_estimees_eur"], sy["reste_a_charge_eur"]
        _para(pdf, f"Tous travaux confondus, y compris ceux à prévoir à l'occasion : "
                   f"{_plage_txt(sy['investissement_eur'])}, aides estimées {_plage_txt(a)} selon vos revenus, "
                   f"reste à charge {_plage_txt(r)}.")
    for cle, libelle in (("economie_chauffage_eur", "Économie de chauffage"),
                         ("economie_eau_chaude_eur", "Économie d'eau chaude")):
        if sy.get(cle):
            _para(pdf, f"{libelle} si tout le plan est réalisé : {_plage_txt(sy[cle])} par an.")
    _para(pdf, f"Première étape conseillée : {sy.get('premiere_action')}.", style="B")


def _hypotheses_v21(pdf: FPDF, audit: dict):
    lignes = _hypotheses_fiche(audit)
    if not lignes:
        return
    _section(pdf, "Hypothèses utilisées")
    for ligne in lignes:
        _puce(pdf, ligne, couleur=TEXTE_2, taille=9)


def _document_ancien(pdf: FPDF, audit: dict, house_label: str | None):
    _entete_ancien(pdf, audit, house_label)
    _section(pdf, "Où votre logement perd de la chaleur")
    _deperditions(pdf, audit)

    c = audit.get("consommation", {})
    v2 = "conso_chauffage_estimee_kwh_an" in c
    _section(pdf, "Consommation")
    if v2:
        _consommation_v2(pdf, audit)
    else:
        _para(pdf, f"Besoin de chauffage estimé : {c.get('besoin_kwh_m2_an')}{NBSP}kWh/m²/an "
                   f"(source : {c.get('origine_besoin')}) × {c.get('surface_m2')}{NBSP}m² "
                   f"= {_kwh(c.get('conso_chauffage_theorique_kwh_an') or 0)} par an.")
        if c.get("conso_elec_declaree_kwh_an"):
            _para(pdf, f"Consommation électrique déclarée : {_kwh(c['conso_elec_declaree_kwh_an'])} par an "
                       f"(écart avec le chauffage théorique : {c.get('ecart_pct')}{NBSP}%).")

    if "gestes" in audit:
        _plan_v21(pdf, audit)
        _synthese_v21(pdf, audit)
        _hypotheses_v21(pdf, audit)
    else:
        _section(pdf, "Vos priorités de travaux, dans l'ordre")
        _priorites_anciennes(pdf, audit, v2)
        _synthese_v1_v2(pdf, audit.get("synthese", {}))
    pdf.ln(4)
    if audit.get("avertissement"):
        _para(pdf, audit["avertissement"], taille=8, couleur=TEXTE_2)


# --- Point d'entrée --------------------------------------------------------------------------

def build_pdf(audit: dict, house_label: str | None = None, fonts_dir: Path | None = None) -> Path:
    pdf = _AuditPDF(fonts_dir or FONTS_DIR)
    pdf.set_title("Pré-audit énergétique Helios")
    pdf.add_page()
    if "plan_recommande" in (audit.get("synthese") or {}):
        _page_en_bref(pdf, audit, house_label)
        pdf.add_page()
        _page_plan(pdf, audit)
        pdf.add_page()
        _page_comprendre(pdf, audit)
        _page_hypotheses(pdf, audit)
    else:
        _document_ancien(pdf, audit, house_label)

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / f"preaudit_{date.today().isoformat()}_{abs(hash(str(audit))) % 10**8}.pdf"
    pdf.output(str(out))
    return out
