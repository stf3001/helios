"""Génération du PDF de pré-audit — doc 07 §6.6.

Utilise fpdf2 (pur Python, aucune dépendance système). Les polices de base couvrent le
latin-1 (accents français) mais pas le symbole « € » : on écrit « EUR ». Le PDF ne fait que
mettre en forme le JSON déterministe du moteur — aucun chiffre n'est (re)calculé ici.
"""

from datetime import date
from pathlib import Path

from fpdf import FPDF
from PIL import Image

from app.core.config import settings

PDF_DIR = Path(__file__).resolve().parents[2] / "generated" / "audits"
_LOGO_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "brand" / "logo-mark.png"

ORANGE = (184, 90, 8)     # primary HELIOS #B85A08 (contraste AA vérifié, cf. tailwind.config.js)
INK = (29, 63, 99)        # bleu marine de la marque — titres
GRIS = (90, 90, 90)
CREAM = (253, 248, 243)   # fond chaleureux de la marque #FDF8F3

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
    return (text or "").replace("€", "EUR").replace("œ", "oe").replace("’", "'").replace("…", "...").encode(
        "latin-1", "replace"
    ).decode("latin-1")


def _eur(n) -> str:
    return f"{int(n):,}".replace(",", " ") + " EUR"


class _AuditPDF(FPDF):
    def header(self):
        # Bandeau chaleureux type "en-tête à lettre" (couleurs de marque, cf. tailwind.config.js)
        self.set_fill_color(*CREAM)
        self.rect(0, 0, self.w, 28, style="F")
        self.set_draw_color(*ORANGE)
        self.set_line_width(0.8)
        self.line(0, 28, self.w, 28)

        if _LOGO_PATH.exists():
            logo_h = 14
            self.image(str(_LOGO_PATH), x=self.l_margin, y=7, h=logo_h)
            # La marque est carree depuis la refonte (`frontend/scripts/brand_assets.py`) :
            # on lit le rapport du fichier plutot que de le reecrire en dur, sinon le
            # titre se decale le jour ou le dessin change de format.
            with Image.open(_LOGO_PATH) as mark:
                ratio = mark.width / mark.height
            text_x = self.l_margin + logo_h * ratio + 4
        else:
            text_x = self.l_margin

        self.set_xy(text_x, 8)
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(*INK)
        self.cell(0, 9, _s("HELIOS"), ln=True)
        self.set_x(text_x)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*ORANGE)
        self.cell(0, 6, _s("Pré-audit énergétique indicatif"), ln=True)

        self.set_y(34)
        self.set_line_width(0.2)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(220, 220, 220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
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
    pdf.set_text_color(*INK)
    pdf.cell(0, 7, _s(titre), ln=True)
    pdf.set_text_color(0, 0, 0)
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
    niveau = _NIVEAU.get(audit.get("niveau"), audit.get("niveau"))
    pdf.cell(0, 5, _s(f"Complétude de la fiche : {_pct(audit.get('completeness_score'))}   -   Niveau : {niveau}"), ln=True)

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
        pdf.cell(0, 6, _s(_pct(part)), ln=True)

    # Consommation — les audits stockés gardent le rendu de leur version.
    c = audit.get("consommation", {})
    v2 = "conso_chauffage_estimee_kwh_an" in c
    v21 = "gestes" in audit
    _section(pdf, "2. Consommation")
    if v2:
        _consommation_v2(pdf, audit)
    else:
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

    if v21:
        _plan_v21(pdf, audit)
        _synthese_v21(pdf, audit)
        _hypotheses_v21(pdf, audit)
    else:
        _section(pdf, "3. Vos priorités de travaux (dans l'ordre)")
        if v2:
            _priorites_v2(pdf, audit.get("priorites", []))
        else:
            _priorites_v1(pdf, audit.get("priorites", []))
        _synthese_v1_v2(pdf, audit.get("synthese", {}))

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / f"preaudit_{date.today().isoformat()}_{abs(hash(str(audit))) % 10**8}.pdf"
    pdf.output(str(out))
    return out


def _synthese_v1_v2(pdf: FPDF, sy: dict):
    _section(pdf, "4. Synthèse")
    if sy.get("nb_actions"):
        aides = sy["aides_estimees_eur"]
        aides_txt = (f"{_eur(aides['bas'])} à {_eur(aides['haut'])} selon vos revenus (barèmes à vérifier)"
                     if isinstance(aides, dict) else _eur(aides))
        _para(pdf,
            f"{sy['nb_actions']} actions recommandées. Investissement total estimé : "
            f"{_eur(sy['investissement_eur']['bas'])} à {_eur(sy['investissement_eur']['haut'])}, "
            f"aides estimées : {aides_txt}."
        )
        if sy.get("economie_annuelle_totale_eur"):
            e = sy["economie_annuelle_totale_eur"]
            _para(pdf, f"Économie annuelle totale potentielle : {_eur(e['bas'])} à {_eur(e['haut'])}.")
        if sy.get("premiere_action"):
            _para(pdf, f"Première étape conseillée : {sy['premiere_action']} (esprit colibri : on commence petit).")
    else:
        _para(pdf, "Aucune action prioritaire détectée : votre logement est déjà bien optimisé.")


_ORIGINE = {
    "dpe": "d'après la lettre DPE",
    "annee_construction": "d'après l'année de construction",
    "defaut": "valeur par défaut, faute de DPE et d'année de construction",
}
_ENERGIE = {"electricite": "électricité", "gaz": "gaz", "fioul": "fioul", "bois": "bois",
            "reseau": "réseau de chaleur"}
_HORIZON = {"maintenant": "Maintenant", "prioritaire": "Prioritaire", "a_l_occasion": "A l'occasion"}
_NIVEAU = {
    "conseils_generaux": "Conseils généraux",
    "prediagnostic_qualitatif": "Pré-diagnostic qualitatif",
    "preaudit_chiffre": "Pré-audit chiffré",
}


def _dec(x, n: int = 1) -> str:
    """Décimale à la française : 0.2001 -> « 0,2001 », 4.1 -> « 4,1 »."""
    if x is None:
        return "-"
    texte = f"{x:.{n}f}" if isinstance(x, float) and n is not None else str(x)
    return texte.replace(".", ",")


def _pct(x) -> str:
    return "-" if x is None else f"{_dec(float(x))} %".replace(",0 %", " %")


def _kwh(n) -> str:
    return f"{int(n):,}".replace(",", " ") + " kWh"


def _plage(f: dict) -> str:
    return f"{_eur(f['bas'])[:-4]}-{_eur(f['haut'])[:-4]}"


def _retour(a: dict) -> str:
    return f"{_dec(float(a['temps_retour_ans']))} ans" if a.get("temps_retour_ans") is not None else "-"


def _tableau(pdf: FPDF, cols: list[tuple[str, int]], lignes: list[list[str]]):
    """Tableau à lignes simples : hauteur fixe, première colonne tronquée si besoin."""
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*CREAM)
    for h, w in cols:
        pdf.cell(w, 6, _s(h), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for ligne in lignes:
        label = _s(ligne[0])
        while pdf.get_string_width(label) > cols[0][1] - 2 and len(label) > 4:
            label = label[:-2]
        pdf.set_x(pdf.l_margin)
        for txt, (_, w) in zip([label, *ligne[1:]], cols):
            pdf.cell(w, 6, _s(txt), border=1)
        pdf.ln()
    pdf.set_font("Helvetica", "", 10)


def _priorites_v1(pdf: FPDF, priorites: list[dict]):
    cols = [("Action", 64), ("Cout", 30), ("Aide", 22), ("Reste", 22), ("Eco/an", 24), ("Retour", 18)]
    _tableau(pdf, cols, [[
        f"#{a['rang']} {a['label']}",
        f"{_eur(a['cout_eur']['bas'])[:-4]}-{_eur(a['cout_eur']['haut'])}",
        _eur(a["aide_estimee_eur"]), _eur(a["reste_a_charge_eur"]),
        _eur(a["economie_annuelle_eur"]["central"]), _retour(a),
    ] for a in priorites])


def _consommation_v2(pdf: FPDF, audit: dict):
    c = audit["consommation"]
    _para(pdf,
        f"Consommation de chauffage estimée : {_kwh(c['conso_chauffage_estimee_kwh_an'])}/an de "
        f"{_ENERGIE.get(c.get('energie_chauffage'), c.get('energie_chauffage'))} "
        f"({_ORIGINE.get(c.get('origine'), c.get('origine'))}, zone climatique {c.get('zone_climatique')})."
    )
    if c.get("conso_chauffage_declaree_kwh_an") is not None:
        _para(pdf,
            f"D'après votre facture : {_kwh(c['conso_elec_declaree_kwh_an'])}/an d'électricité, dont environ "
            f"{_kwh(c['usages_specifiques_kwh_an'])} pour les usages courants (appareils, eau chaude) : "
            f"il reste {_kwh(c['conso_chauffage_declaree_kwh_an'])} pour le chauffage."
        )
    if c.get("message_ratio"):
        _para(pdf, c["message_ratio"])
    for alerte in audit.get("alertes", []):
        _para(pdf, f"Attention : {alerte}")
    _para(pdf,
        f"Les économies portent sur {_kwh(c['conso_chauffage_retenue_kwh_an'])}/an de chauffage, au prix "
        f"de {_dec(c['prix_energie_eur_kwh'], 4)} EUR/kWh, soit environ {_eur(c['cout_chauffage_actuel_eur'])}/an."
    )


def _priorites_v2(pdf: FPDF, priorites: list[dict]):
    cols = [("Action", 50), ("Cout", 28), ("Aide*", 24), ("Reste", 26), ("Eco/an", 18), ("Retour", 18),
            ("Quand", 22)]
    _tableau(pdf, cols, [[
        f"#{a['rang']} {a['label']}", _plage(a["cout_eur"]), _plage(a["aide_estimee_eur"]),
        _plage(a["reste_a_charge_eur"]), _eur(a["economie_annuelle_eur"]["central"])[:-4], _retour(a),
        _HORIZON.get(a.get("horizon"), "-"),
    ] for a in priorites])
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, "Montants en EUR. * Aides selon vos revenus, barèmes à vérifier. L'économie de chaque "
               "action tient compte de celles qui la précèdent.")
    pdf.set_font("Helvetica", "", 10)
    occasion = [a for a in priorites if a.get("horizon") == "a_l_occasion"]
    if occasion:
        _para(pdf, "A faire à l'occasion, pas en priorité (le temps de retour seul ne le justifie pas) :")
        for a in occasion:
            _para(pdf, f"- {a['label']} : {a.get('libelle_occasion') or 'lors de travaux sur ce poste'}.")


# --- v2.1 : « Votre plan » en quatre temps, confort d'été, hypothèses ---------------------

def _sous_titre(pdf: FPDF, titre: str):
    pdf.ln(1)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 6, _s(titre), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)


def _puces(pdf: FPDF, lignes: list[str]):
    for ligne in lignes:
        _para(pdf, f"- {ligne}")


def _table_actions(pdf: FPDF, actions: list[dict]):
    cols = [("Action", 62), ("Cout", 28), ("Aide*", 26), ("Reste", 28), ("Eco/an", 22), ("Retour", 20)]
    _tableau(pdf, cols, [[
        a["label"], _plage(a["cout_eur"]), _plage(a["aide_estimee_eur"]), _plage(a["reste_a_charge_eur"]),
        _eur(a["economie_annuelle_eur"]["central"])[:-4], _retour(a),
    ] for a in actions])
    notes = [f"{a['label']} : {a['contexte']}." for a in actions if a.get("contexte")]
    notes += [f"{a['label']} - aide : {a['aide_note']}." for a in actions if a.get("aide_note")]
    if notes:
        pdf.set_font("Helvetica", "I", 8)
        for n in notes:
            _para(pdf, n)
        pdf.set_font("Helvetica", "", 10)


def _plan_v21(pdf: FPDF, audit: dict):
    sy = audit.get("synthese", {})
    travaux = [a for a in audit.get("priorites", []) if a.get("categorie") != "production"]
    par = {h: [a for a in travaux if a.get("horizon") == h] for h in ("maintenant", "prioritaire", "a_l_occasion")}

    _section(pdf, "3. Votre plan")
    _para(pdf, f"{sy.get('decompte', '')}. Première étape : {sy.get('premiere_action')}.")
    if sy.get("message_sans_isolation"):
        _para(pdf, sy["message_sans_isolation"])

    _sous_titre(pdf, "Maintenant")
    _puces(pdf, [g["texte"] for g in audit.get("gestes", [])])
    _puces(pdf, [c["texte"] for c in audit.get("conseils_equipements", [])])
    if par["maintenant"]:
        _table_actions(pdf, par["maintenant"])

    _sous_titre(pdf, "Cette année")
    if par["prioritaire"]:
        _table_actions(pdf, par["prioritaire"])
    else:
        _para(pdf, "Aucun investissement ne se justifie à court terme : les gestes ci-dessus suffisent pour l'instant.")

    _sous_titre(pdf, "A l'occasion de...")
    if par["a_l_occasion"]:
        _puces(pdf, [f"{a['label']} : {a.get('libelle_occasion') or 'lors de travaux sur ce poste'}."
                     for a in par["a_l_occasion"]])
        _table_actions(pdf, par["a_l_occasion"])
    else:
        _para(pdf, "Rien à prévoir pour l'instant.")
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, "Montants en EUR. * Aides selon vos revenus, du plus élevé au plus modeste : barèmes 2026 "
               "de notre base (relevé du 22/07/2026) ou à vérifier. L'économie de chauffage de chaque "
               "action tient compte de celles qui la précèdent ; l'eau chaude se compte à part.")
    pdf.set_font("Helvetica", "", 10)

    sol = audit.get("solaire")
    if sol:
        _sous_titre(pdf, "Pour aller plus loin")
        if sol["type"] == "piste":
            _para(pdf, sol["texte"])
        else:
            e = sol["etude"]
            kwc = f"{_dec(float(e['puissance_kwc']))} kWc" if e.get("puissance_kwc") is not None else "-"
            lignes = [f"Installation étudiée : {kwc}" + (f" ({e['option']})" if e.get("option") else "")]
            if e.get("investissement_eur") is not None:
                lignes.append(f"Investissement : {_eur(e['investissement_eur'])}")
            if e.get("economie_1re_annee_eur") is not None:
                lignes.append(f"Économie la première année : {_eur(e['economie_1re_annee_eur'])}")
            if e.get("temps_retour_ans") is not None:
                lignes.append(f"Temps de retour : {_dec(float(e['temps_retour_ans']))} ans")
            if e.get("gain_net_25_ans_eur") is not None:
                lignes.append(f"Gain net sur 25 ans : {_eur(e['gain_net_25_ans_eur'])}")
            if e.get("autonomie_pct") is not None:
                lignes.append(f"Autonomie : {_pct(e['autonomie_pct'])}")
            _puces(pdf, lignes)
            _para(pdf, f"Source : {sol['source']}." + (f" {sol['mention'].capitalize()}." if sol.get("mention") else ""))

    ete = audit.get("confort_ete")
    if ete:
        _section(pdf, "4. Confort d'été")
        _puces(pdf, ete["conseils"])
        if ete.get("note_combles"):
            _para(pdf, ete["note_combles"])


def _synthese_v21(pdf: FPDF, audit: dict):
    sy = audit.get("synthese", {})
    _section(pdf, "5. Synthèse" if audit.get("confort_ete") else "4. Synthèse")
    _para(pdf, f"{sy.get('decompte', '')}.")
    if sy.get("nb_actions"):
        a, r = sy["aides_estimees_eur"], sy["reste_a_charge_eur"]
        _para(pdf,
            f"Travaux chiffrés : {_eur(sy['investissement_eur']['bas'])} à {_eur(sy['investissement_eur']['haut'])}, "
            f"aides estimées {_eur(a['bas'])} à {_eur(a['haut'])} selon vos revenus, "
            f"reste à charge {_eur(r['bas'])} à {_eur(r['haut'])}."
        )
    for cle, libelle in (("economie_chauffage_eur", "Économie de chauffage"),
                         ("economie_eau_chaude_eur", "Économie d'eau chaude")):
        if sy.get(cle):
            _para(pdf, f"{libelle} si tout le plan est réalisé : {_eur(sy[cle]['bas'])} à {_eur(sy[cle]['haut'])} par an.")
    _para(pdf, f"Première étape conseillée : {sy.get('premiere_action')} (esprit colibri : on commence petit).")


def _hypotheses_v21(pdf: FPDF, audit: dict):
    lignes = [h["valeur"] for h in audit.get("hypotheses", [])
              if h.get("source") == "Fiche Maison" and isinstance(h.get("valeur"), str)]
    if not lignes:
        return
    _section(pdf, "6. Hypothèses utilisées" if audit.get("confort_ete") else "5. Hypothèses utilisées")
    pdf.set_font("Helvetica", "", 9)
    _puces(pdf, [l[0].upper() + l[1:] for l in lignes])
    pdf.set_font("Helvetica", "", 10)
