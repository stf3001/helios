"""Génération du PDF de pré-audit — doc 07 §6.6.

Utilise fpdf2 (pur Python, aucune dépendance système). Les polices de base couvrent le
latin-1 (accents français) mais pas le symbole « € » : on écrit « EUR ». Le PDF ne fait que
mettre en forme le JSON déterministe du moteur — aucun chiffre n'est (re)calculé ici.
"""

from datetime import date
from pathlib import Path

from fpdf import FPDF

from app.core.config import settings

PDF_DIR = Path(__file__).resolve().parents[2] / "generated" / "audits"

ORANGE = (232, 135, 30)   # primary HELIOS #E8871E
GRIS = (90, 90, 90)

_POSTE_LABEL = {
    "toiture": "Toiture / combles",
    "murs": "Murs",
    "air_ventilation": "Air / ventilation",
    "menuiseries": "Menuiseries",
    "plancher": "Plancher bas",
    "ponts_thermiques": "Ponts thermiques",
}


def _s(text: str) -> str:
    """Rend une chaîne compatible police latin-1 (remplace € et caractères hors jeu)."""
    return (text or "").replace("€", "EUR").replace("œ", "oe").replace("’", "'").encode(
        "latin-1", "replace"
    ).decode("latin-1")


def _eur(n) -> str:
    return f"{int(n):,}".replace(",", " ") + " EUR"


class _AuditPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*ORANGE)
        self.cell(0, 10, _s("HELIOS"), ln=True)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GRIS)
        self.cell(0, 6, _s("Pré-audit énergétique indicatif"), ln=True)
        self.ln(2)
        self.set_draw_color(*ORANGE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GRIS)
        self.multi_cell(0, 3, _s(
            "Pré-diagnostic indicatif (ordres de grandeur), ne remplace pas un audit réalisé par un "
            "professionnel certifié. Coûts, aides et économies à confirmer."
        ), align="C")


def _usable_width(pdf: FPDF) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def _section(pdf: FPDF, titre: str):
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, _s(titre), ln=True)
    pdf.set_font("Helvetica", "", 10)


def _para(pdf: FPDF, text: str):
    """Paragraphe robuste : remet X à la marge et impose une largeur explicite (évite les erreurs fpdf)."""
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_usable_width(pdf), 5, _s(text))


def build_pdf(audit: dict, house_label: str | None = None) -> Path:
    pdf = _AuditPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # En-tête maison
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, _s(f"Date : {date.today().strftime('%d/%m/%Y')}   -   Version moteur : {audit.get('version_helios', '')}"), ln=True)
    if house_label:
        pdf.cell(0, 5, _s(f"Logement : {house_label}"), ln=True)
    pdf.cell(0, 5, _s(f"Complétude de la fiche : {audit.get('completeness_score')}%   -   Niveau : {audit.get('niveau')}"), ln=True)

    # Déperditions
    _section(pdf, "1. Où votre logement perd de la chaleur")
    for d in audit.get("deperditions", []):
        label = _POSTE_LABEL.get(d["poste"], d["poste"])
        part = d["part_pct"]
        pdf.cell(55, 6, _s(label), border=0)
        # barre proportionnelle
        x, y = pdf.get_x(), pdf.get_y()
        pdf.set_fill_color(*ORANGE)
        pdf.rect(x, y + 1, max(1.0, part * 1.2), 4, style="F")
        pdf.set_x(x + 130)
        pdf.cell(0, 6, _s(f"{part} %"), ln=True)

    # Consommation
    c = audit.get("consommation", {})
    _section(pdf, "2. Consommation")
    _para(pdf,
        f"Besoin de chauffage estimé : {c.get('besoin_kwh_m2_an')} kWh/m2/an "
        f"(source : {c.get('origine_besoin')}) x {c.get('surface_m2')} m2 "
        f"= {c.get('conso_chauffage_theorique_kwh_an')} kWh/an."
    )
    if c.get("conso_elec_declaree_kwh_an"):
        _para(pdf,
            f"Conso électrique déclarée : {c['conso_elec_declaree_kwh_an']} kWh/an "
            f"(écart vs théorique chauffage : {c.get('ecart_pct')} %)."
        )

    # Priorités — tableau à lignes simples (cellules de hauteur fixe, label tronqué si besoin)
    _section(pdf, "3. Vos priorités de travaux (dans l'ordre)")
    cols = [("Action", 64), ("Cout", 30), ("Aide", 22), ("Reste", 22), ("Eco/an", 24), ("Retour", 18)]
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    for h, w in cols:
        pdf.cell(w, 6, _s(h), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for a in audit.get("priorites", []):
        retour = f"{a['temps_retour_ans']} ans" if a.get("temps_retour_ans") is not None else "-"
        label = _s(f"#{a['rang']} {a['label']}")
        while pdf.get_string_width(label) > 62 and len(label) > 4:  # tronque au besoin
            label = label[:-2]
        cells = [
            (label, 64),
            (f"{_eur(a['cout_eur']['bas'])[:-4]}-{_eur(a['cout_eur']['haut'])}", 30),
            (_eur(a["aide_estimee_eur"]), 22),
            (_eur(a["reste_a_charge_eur"]), 22),
            (_eur(a["economie_annuelle_eur"]["central"]), 24),
            (retour, 18),
        ]
        pdf.set_x(pdf.l_margin)
        for txt, w in cells:
            pdf.cell(w, 6, _s(txt), border=1)
        pdf.ln()

    # Synthèse
    sy = audit.get("synthese", {})
    _section(pdf, "4. Synthèse")
    if sy.get("nb_actions"):
        _para(pdf,
            f"{sy['nb_actions']} actions recommandées. Investissement total estimé : "
            f"{_eur(sy['investissement_eur']['bas'])} à {_eur(sy['investissement_eur']['haut'])}, "
            f"aides estimées : {_eur(sy['aides_estimees_eur'])}."
        )
        if sy.get("economie_annuelle_totale_eur"):
            e = sy["economie_annuelle_totale_eur"]
            _para(pdf, f"Économie annuelle totale potentielle : {_eur(e['bas'])} à {_eur(e['haut'])}.")
        _para(pdf, f"Première étape conseillée : {sy['premiere_action']} (esprit colibri : on commence petit).")
    else:
        _para(pdf, "Aucune action prioritaire détectée : votre logement est déjà bien optimisé.")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / f"preaudit_{date.today().isoformat()}_{abs(hash(str(audit))) % 10**8}.pdf"
    pdf.output(str(out))
    return out
