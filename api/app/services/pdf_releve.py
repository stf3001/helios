"""PDF du relevé mensuel d'un partenaire (mises en relation, lot 4).

Mêmes polices et briques que le pré-audit et le dossier de la maison : tout est IMPORTÉ de
`pdf_audit.py`, rien n'y est modifié. Le document ne présente que l'instantané calculé par
`services/releves.py` : aucune donnée de foyer n'y entre (code postal seulement).

En tête, la mention exacte voulue par Stéphane : un relevé N'EST PAS une facture.
"""
from datetime import date, datetime
from pathlib import Path

from fpdf.enums import XPos, YPos
from PIL import Image

from app.services.pdf_audit import (
    _LOGO_PATH, ACCENT, BORD, FONTS_DIR, INK, SABLE, TEXTE_2, _AuditPDF, _largeur, _para, _section, _tableau,
    _titre_page,
)

MENTION = "Relevé de mises en relation — ce document n'est pas une facture."
PROVISOIRE = ("PROVISOIRE — le mois n'est pas clos : les montants peuvent encore changer (contestations en "
              "cours ou à venir dans le délai de 7 jours).")
ETATS = {"facturable": "Facturable", "contestation_en_cours": "Contestation en cours",
         "contestation_acceptee": "Contestation acceptée"}
METIERS = {"solaire": "Panneaux solaires", "pac": "Pompe à chaleur", "isolation": "Isolation",
           "eau": "Machine à eau de l'air", "eolien": "Éolienne", "inertie": "Stockage par inertie"}
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre")


def nom_du_mois(mois: str) -> str:
    annee, m = (int(x) for x in mois.split("-"))
    return f"{MOIS[m - 1]} {annee}"


def _eur(x: float) -> str:
    entier, dec = f"{x:,.2f}".split(".")
    return f"{entier.replace(',', ' ')},{dec} €"


def _jour(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


class _RelevePDF(_AuditPDF):
    def header(self):
        y = 10
        x = self.l_margin
        if _LOGO_PATH.exists():
            with Image.open(_LOGO_PATH) as mark:
                ratio = mark.width / mark.height
            self.image(str(_LOGO_PATH), x=self.l_margin, y=y, h=8)
            x = self.l_margin + 8 * ratio + 3
        self.set_xy(x, y)
        self.police("serif", "", 17)
        self.set_text_color(*INK)
        self.cell(40, 8, "Helios")
        self.police("sans", "", 8.5)
        self.set_text_color(*TEXTE_2)
        self.set_xy(self.l_margin, y + 1)
        self.cell(0, 6, "Relevé de mises en relation", align="R")
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
        self.cell(largeur - 20, 4, MENTION)
        self.cell(20, 4, f"{self.page_no()} / {{nb}}", align="R")
        self.set_text_color(*INK)


def releve_pdf(r: dict, statut: str, fonts_dir: Path = FONTS_DIR) -> bytes:
    """`r` : un relevé de `releves.releve` (ou son instantané clos) ; `statut` : `clos` ou `provisoire`."""
    pdf = _RelevePDF(fonts_dir)
    pdf.set_title(f"Relevé {r['mois']} — {r['partenaire']['raison_sociale']}")
    pdf.add_page()

    # La mention, en tête et en clair, avant tout chiffre.
    pdf.police("sans", "B", 10)
    pdf.set_fill_color(*SABLE)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(_largeur(pdf), 5.5, MENTION, fill=True, padding=2.5, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*INK)
    pdf.ln(3)

    sous = r["partenaire"]["raison_sociale"]
    if r["partenaire"].get("siret"):
        sous += f" · SIRET {r['partenaire']['siret']}"
    if statut == "clos" and r.get("cloture_le"):
        sous += f" · clos le {datetime.fromisoformat(r['cloture_le']).strftime('%d/%m/%Y')}"
    _titre_page(pdf, f"Relevé de {nom_du_mois(r['mois'])}", sous)
    if statut != "clos":
        _para(pdf, PROVISOIRE, taille=9, style="B", couleur=ACCENT)
        pdf.ln(1)
    _para(pdf, "Une ligne par mise en relation transmise dans le mois (heure de Paris), au prix fixe en vigueur à "
               "sa transmission. Une contestation en cours est exclue du total tant qu'elle n'est pas tranchée ; "
               "acceptée, la ligne n'est pas due.", taille=8.5, couleur=TEXTE_2)
    pdf.ln(1)

    _section(pdf, "Mises en relation", f"{r['nb_lignes']} ligne(s)")
    lignes = [[f"{_jour(x['date'])} {x['heure']}", METIERS.get(x["metier"], x["metier"] or "—"),
               x["code_postal"] or "—", ETATS[x["etat"]] + (" (contestation refusée)" if x["contestation_refusee"] else ""),
               _eur(x["prix_ht"])] for x in r["lignes"]]
    if lignes:
        _tableau(pdf, ["Transmise le", "Travaux", "Code postal", "État", "Prix HT"], [30, 40, 24, 58, 28], lignes,
                 ["LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"])
    else:
        _para(pdf, "Aucune mise en relation ce mois-ci.")

    _section(pdf, "Total")
    _tableau(pdf, ["", "Montant"], [152, 28], [
        [f"Total HT ({r['nb_facturables']} ligne(s) facturable(s))", f"**{_eur(r['total_ht'])}**"],
        [f"TVA {round(r['tva_taux'] * 100):d} % (indicative)", _eur(r["tva"])],
        ["TTC (indicatif)", _eur(r["ttc"])],
    ], ["LEFT", "RIGHT"])
    if r["en_attente"]:
        _para(pdf, f"{len(r['en_attente'])} contestation(s) en cours, exclue(s) du total : "
                   + " ; ".join(f"{_jour(x['date'])}, {METIERS.get(x['metier'], x['metier'])} ({x['code_postal']})"
                                for x in r["en_attente"]) + ".", taille=8.5, couleur=TEXTE_2)
    return bytes(pdf.output())
