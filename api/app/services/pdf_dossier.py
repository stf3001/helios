"""Le « Dossier de la maison » en PDF (carnet de maison, lot 6) — gratuit, généré à la demande.

Il suit les rubriques d'un carnet d'information du logement SANS en être un : jamais
« conforme », « certifié » ni « officiel » dans le document (décision de Stéphane). Il ne
fait que METTRE EN FORME ce que la fiche et les moteurs des lots 1 à 4 ont produit : aucun
chiffre n'est recalculé ici, pas même une somme. Le PDL n'y figure jamais ; les numéros de
série seulement si le foyer le demande.

Mise en page : les briques du pré-audit (`pdf_audit.py`) sont IMPORTÉES, pas extraites —
polices et repli Helvetica, couleurs, sections, tableaux. Le pré-audit n'a donc pas bougé
d'un octet. Les libellés des codes sont recopiés de l'écran (`components/carnet/libelles.ts`,
`libellesPieces.ts`, `pages/FicheMaison.tsx`) : les trois se tiennent à jour ENSEMBLE.
"""
from datetime import date
from pathlib import Path

from fpdf.enums import XPos, YPos
from PIL import Image

from app.services.pdf_audit import (
    _LOGO_PATH, BORD, FONTS_DIR, INK, SABLE, TEXTE_2, _AuditPDF, _largeur, _para, _place, _section, _tableau,
    _titre_page,
)

SECTIONS = ("logement", "enveloppe", "equipements", "pieces", "travaux", "entretien", "energie", "documents")
TITRES = {
    "logement": "Le logement", "enveloppe": "L'enveloppe", "equipements": "Les équipements",
    "pieces": "Les pièces et leurs émetteurs", "travaux": "Les travaux et les garanties",
    "entretien": "L'entretien", "energie": "L'énergie déclarée", "documents": "Les documents disponibles",
}

# Décision de Stéphane (carnet, lot 11), recopiée telle quelle après vérification des rubriques
# sur les textes (CCH L. 126-35-2 et suivants, arrêté du 27/12/2022) — point 44 de TODO.md.
MENTION = ("Ce dossier rassemble les informations déclarées par le propriétaire dans Hélios, selon les "
           "rubriques du carnet d'information du logement (code de la construction et de l'habitation, "
           "art. L. 126-35-2 et suivants). Il ne remplace pas les documents remis par les professionnels et ne "
           "vaut pas attestation.")
MENTION_GARANTIES = "À vérifier sur votre contrat et l'attestation d'assurance de l'entreprise."
LEGENDE = ("Chaque valeur porte une marque : (D) déclaré, saisi par le propriétaire · (J) justifié, un document "
           "est joint dans Hélios · (S) supposé, déduit d'une information incomplète (une année sans date) · "
           "(C) calculé par Hélios à partir de ces données.")
NON_RENSEIGNE = "Non renseigné."
MOIS_JOURNAL = 24

# --- Libellés (copies de l'écran) ---------------------------------------------------------

_FICHE = {
    "type_logement": {"maison": "Maison", "appartement": "Appartement"},
    "statut": {"proprietaire": "Propriétaire", "locataire": "Locataire", "en_achat": "En cours d'achat"},
    "annee_construction": {"avant_1948": "Avant 1948", "1948_1974": "1948 – 1974", "1975_1988": "1975 – 1988",
                           "1989_2000": "1989 – 2000", "2001_2012": "2001 – 2012", "apres_2012": "Après 2012"},
    "isolation": {"aucune": "Aucune", "partielle": "Partielle", "bonne": "Bonne", "inconnue": "Inconnue"},
    "menuiseries": {"simple": "Simple vitrage", "double": "Double vitrage", "double_recent": "Double vitrage récent",
                    "triple": "Triple vitrage"},
    "ventilation": {"aucune": "Aucune", "naturelle": "Naturelle", "VMC_simple": "VMC simple flux",
                    "VMC_double": "VMC double flux", "inconnue": "Inconnue"},
    "option_tarifaire": {"base": "Base", "HPHC": "Heures pleines / heures creuses", "tempo": "Tempo"},
    # Pré-audit lot 7 : recopiés de `FicheMaison.tsx` (à tenir ENSEMBLE).
    "conso_autre_energie_type": {"gaz": "Gaz", "fioul": "Fioul", "bois_buches": "Bois (bûches)",
                                 "granules": "Granulés", "reseau": "Réseau de chaleur"},
    "conso_autre_energie_unite": {"kwh": "kWh", "m3": "m³", "litres": "litres", "steres": "stères", "kg": "kg"},
}
_CATEGORIES = {
    "chauffage": "Chauffage", "ecs": "Eau chaude", "clim": "Climatisation", "ventilation": "Ventilation",
    "production_electricite": "Production d'électricité", "stockage": "Stockage",
    "recharge": "Recharge du véhicule", "eau": "Eau et assainissement", "autre": "Autre",
}
_TYPES = {
    "PAC_air_eau": "PAC air/eau", "PAC_air_air": "PAC air/air", "chaudiere_gaz": "Chaudière gaz",
    "chaudiere_fioul": "Chaudière fioul", "chaudiere_bois": "Chaudière bois", "poele_bois": "Poêle à bois",
    "poele_granules": "Poêle à granulés", "insert": "Insert ou foyer fermé", "convecteurs": "Convecteurs électriques",
    "radiateurs_inertie": "Radiateurs à inertie", "ballon_elec": "Ballon électrique",
    "thermodynamique": "Ballon thermodynamique", "gaz": "Chauffe-eau gaz", "solaire": "Chauffe-eau solaire",
    "instantane": "Chauffe-eau instantané", "split": "Split", "multisplit": "Multisplit", "gainable": "Gainable",
    "VMC_simple": "VMC simple flux", "VMC_double": "VMC double flux", "panneaux_pv": "Panneaux photovoltaïques",
    "onduleur": "Onduleur", "eolienne": "Éolienne", "batterie": "Batterie", "borne_recharge": "Borne de recharge",
    "adoucisseur": "Adoucisseur", "fosse_septique": "Fosse septique", "micro_station": "Micro-station d'épuration",
    "pompe_piscine": "Pompe de piscine", "generateur_eau_atmospherique": "Générateur d'eau atmosphérique",
    "autre": "Autre",
}
_PIECES = {
    "sejour": "Séjour", "cuisine": "Cuisine", "chambre": "Chambre", "salle_de_bain": "Salle de bain", "wc": "WC",
    "bureau": "Bureau", "entree": "Entrée", "buanderie": "Buanderie", "garage": "Garage", "veranda": "Véranda",
    "combles_amenages": "Combles aménagés", "autre": "Autre",
}
# [singulier, pluriel] — « 2 radiateurs à eau » (copie de `libellesPieces.ts`).
_EMETTEURS = {
    "radiateur_eau": ("radiateur à eau", "radiateurs à eau"), "convecteur": ("convecteur", "convecteurs"),
    "panneau_rayonnant": ("panneau rayonnant", "panneaux rayonnants"),
    "radiateur_inertie": ("radiateur à inertie", "radiateurs à inertie"),
    "seche_serviettes": ("sèche-serviettes", "sèche-serviettes"),
    "plancher_chauffant_eau": ("plancher chauffant à eau", "planchers chauffants à eau"),
    "plancher_chauffant_elec": ("plancher chauffant électrique", "planchers chauffants électriques"),
    "unite_interieure_clim": ("unité de climatisation", "unités de climatisation"),
    "poele_bois": ("poêle à bois", "poêles à bois"), "poele_granules": ("poêle à granulés", "poêles à granulés"),
    "cheminee": ("cheminée", "cheminées"), "autre": ("autre émetteur", "autres émetteurs"),
}
_JOURNAL = {"entretien": "Entretien", "controle": "Contrôle", "reparation": "Réparation",
            "remplacement": "Remplacement", "amelioration": "Amélioration", "autre": "Autre", "travaux": "Travaux"}
_ECHEANCES = {"en_retard": "en retard", "ce_mois": "ce mois-ci", "bientot": "dans les 3 mois",
              "a_planifier": "à planifier", "plus_tard": "plus tard"}
_GARANTIES = {"en_cours": "en cours", "bientot": "se termine bientôt", "expiree": "terminée"}
_DOCUMENTS = {"dpe": "DPE", "facture": "Facture", "devis": "Devis", "photo": "Photo", "plan": "Plan",
              "autre": "Autre"}
# Carnet, lot 11 (copies de `libelles.ts`).
_EVACUATIONS = {"ventouse": "ventouse", "conduit": "conduit", "sans_objet": "sans objet", "inconnu": ""}
_CATEGORIES_CIL = {
    "isolation_toiture": "Isolation de la toiture", "isolation_murs": "Isolation des murs",
    "parois_vitrees_portes": "Fenêtres et portes", "planchers_bas": "Planchers bas",
    "chauffage_froid_ecs": "Chauffage, froid, eau chaude", "autre": "Hors carnet",
}
_ORIENTATIONS = {"N": "nord", "NE": "nord-est", "E": "est", "SE": "sud-est", "S": "sud", "SO": "sud-ouest",
                 "O": "ouest", "NO": "nord-ouest"}
_QUI = {"soi": "vous-même", "pro": "un professionnel", "soi_ou_pro": "vous ou un pro"}


# --- Petites mises en forme (aucun calcul) ------------------------------------------------

def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _txt(v) -> str:
    """Une saisie du foyer, neutralisée pour le markdown des tableaux (`__`, `**`…)."""
    if v is None:
        return ""
    s = str(v)
    for seq in ("**", "__", "~~", "--"):
        s = s.replace(seq, seq[0] + " " + seq[1])
    return s


def _date(d) -> str:
    return d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else ""


def _nombre(n, unite: str = "", decimales: int = 1) -> str:
    if n is None:
        return ""
    entier = float(n).is_integer()
    texte = f"{int(n):,}".replace(",", " ") if entier else f"{n:,.{decimales}f}".replace(",", " ").replace(".", ",")
    return f"{texte} {unite}".strip()


def _marque(code: str) -> str:
    """(D), (J), (S), (C). Pas d'italique : un J penché se lisait comme une barre oblique."""
    return f"({code})"


def _sous_titre(pdf, texte: str, couleur=INK):
    """Un sous-titre ne reste jamais seul en bas de page : il part avec l'en-tête du tableau."""
    _place(pdf, 28)
    _para(pdf, texte, taille=9.5, style="B", couleur=couleur)


def _rempli(v) -> bool:
    return v not in (None, "", [])


class _DossierPDF(_AuditPDF):
    def __init__(self, fonts_dir: Path, aujourd_hui: date):
        self.aujourd_hui = aujourd_hui
        super().__init__(fonts_dir)
        # La première page porte la mention en pied : il lui faut plus de place en bas.
        self.set_auto_page_break(auto=True, margin=34)

    def header(self):
        """Même en-tête que le pré-audit (logo, « Helios »), libellé du document à droite."""
        if self.page_no() > 1:
            self.set_auto_page_break(auto=True, margin=18)
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
        self.cell(0, 6, "Dossier de la maison", align="R")
        self.set_draw_color(*BORD)
        self.set_line_width(0.3)
        self.line(self.l_margin, y + 11, self.w - self.r_margin, y + 11)
        self.set_y(y + 16)
        self.set_text_color(*INK)

    def footer(self):
        largeur = self.w - self.l_margin - self.r_margin
        if self.page_no() == 1:
            self.set_y(-32)
            self.police("sans", "I", 7)
            self.set_text_color(*TEXTE_2)
            self.multi_cell(largeur, 3.6, MENTION, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(-14)
        self.set_draw_color(*BORD)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.police("sans", "", 7)
        self.set_text_color(*TEXTE_2)
        self.cell(largeur - 20, 4, f"Généré le {_date(self.aujourd_hui)} · Hélios")
        self.cell(20, 4, f"{self.page_no()} / {{nb}}", align="R")
        self.set_text_color(*INK)


# --- Les sections -------------------------------------------------------------------------

def _fiche(pdf, lignes: list[tuple[str, str, str]]):
    """Rubrique · valeur · marque. Une ligne vide n'est pas affichée."""
    lignes = [l for l in lignes if l[1]]
    if not lignes:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    _tableau(pdf, ["Rubrique", "Valeur", ""], [55, 113, 12], [[r, _txt(v), _marque(m)] for r, v, m in lignes])


def _logement(pdf, h):
    oui_non = {True: "Oui", False: "Non"}
    _fiche(pdf, [
        ("Code postal", _champ(h, "code_postal"), "D"),
        ("Type de logement", _FICHE["type_logement"].get(_champ(h, "type_logement"), ""), "D"),
        ("Statut de l'occupant", _FICHE["statut"].get(_champ(h, "statut"), ""), "D"),
        ("Période de construction", _FICHE["annee_construction"].get(_champ(h, "annee_construction"), ""), "D"),
        ("Surface habitable", _nombre(_champ(h, "surface_habitable"), "m²"), "D"),
        ("Niveaux", _nombre(_champ(h, "nb_niveaux")), "D"),
        ("Résidence principale", oui_non.get(_champ(h, "residence_principale"), ""), "D"),
    ])


def _enveloppe(pdf, h, dpe_justifie: bool):
    def isol(champ):
        niveau = _FICHE["isolation"].get(_champ(h, champ), "")
        annee = _champ(h, f"{champ}_annee")
        return f"{niveau} ({annee})" if niveau and annee else niveau

    dpe = _champ(h, "dpe_lettre") or ""
    if dpe and _champ(h, "dpe_annee"):
        dpe = f"{dpe} ({_champ(h, 'dpe_annee')})"
    menuis = _FICHE["menuiseries"].get(_champ(h, "menuiseries"), "")
    if menuis and _champ(h, "menuiseries_annee"):
        menuis = f"{menuis} ({_champ(h, 'menuiseries_annee')})"
    _fiche(pdf, [
        ("Isolation des combles", isol("isolation_combles"), "D"),
        ("Isolation des murs", isol("isolation_murs"), "D"),
        ("Isolation du plancher", isol("isolation_plancher"), "D"),
        ("Menuiseries", menuis, "D"),
        ("Ventilation", _FICHE["ventilation"].get(_champ(h, "ventilation"), ""), "D"),
        ("DPE", dpe, "J" if dpe_justifie else "D"),
    ])


def _equipements(pdf, equipements, numeros_serie: bool):
    if not equipements:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    entetes = ["Type", "Marque et modèle", "Pose", "Âge", "Garantie fabricant", "Contrat", "Évacuation, étiquette"]
    largeurs = [30, 34, 22, 15, 24, 27, 28]
    if numeros_serie:
        entetes.append("N° de série")
        largeurs = [25, 27, 20, 13, 21, 22, 25, 27]

    def ligne(e):
        pose = (_date(_champ(e, "date_pose")) if _champ(e, "date_pose")
                else (f"vers {_champ(e, 'annee_pose')}" if _champ(e, "annee_pose") else ""))
        age = _champ(e, "age_ans")
        age_txt = f"{age} an{'s' if age and age > 1 else ''} {_marque('S' if _champ(e, 'age_statut') == 'suppose' else 'C')}" \
            if age is not None else ""
        contrat = {True: "Oui", False: "Non"}.get(_champ(e, "contrat_entretien"), "")
        if contrat == "Oui" and _champ(e, "contrat_prestataire"):
            contrat = f"Oui, {_txt(_champ(e, 'contrat_prestataire'))}"
        cellules = [
            f"{_TYPES.get(_champ(e, 'type'), _champ(e, 'type'))} {_marque('D')}",
            _txt(" ".join(x for x in (_champ(e, "marque"), _champ(e, "modele")) if x)),
            f"{pose} {_marque('D')}" if pose else "",
            age_txt,
            f"{_date(_champ(e, 'garantie_fabricant_fin'))} {_marque('D')}" if _champ(e, "garantie_fabricant_fin") else "",
            contrat,
            ", ".join(x for x in (_EVACUATIONS.get(_champ(e, "mode_evacuation") or "", ""),
                                  "" if _champ(e, "etiquette_energie") in (None, "inconnue")
                                  else f"classe {_champ(e, 'etiquette_energie')}") if x),
        ]
        if numeros_serie:
            cellules.append(_txt(_champ(e, "numero_serie")))
        return cellules

    en_service = [e for e in equipements if _champ(e, "en_service") is not False]
    anciens = [e for e in equipements if _champ(e, "en_service") is False]
    for code, libelle in _CATEGORIES.items():
        groupe = [e for e in en_service if _champ(e, "categorie") == code]
        if groupe:
            _sous_titre(pdf, libelle)
            _tableau(pdf, entetes, largeurs, [ligne(e) for e in groupe])
    if anciens:
        _sous_titre(pdf, "Anciens équipements (déposés ou remplacés)", couleur=TEXTE_2)
        _tableau(pdf, entetes, largeurs, [ligne(e) for e in anciens])


def _pieces(pdf, pieces, emetteurs, resume):
    if not pieces:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    if resume:
        morceaux = [f"{resume['nb_pieces']['valeur']} pièces, dont {resume['nb_chauffees']['valeur']} chauffées"]
        if resume["surface_pieces_m2"]["valeur"]:
            morceaux.append(f"{_nombre(resume['surface_pieces_m2']['valeur'], 'm²')} déclarés (hors garage)")
        _para(pdf, " · ".join(morceaux) + " " + _marque("C"), taille=9, couleur=TEXTE_2)
        for ecart in (resume.get("ecart_surface"), resume.get("ecart_clim")):
            if ecart:
                _para(pdf, f"{ecart['message']} {_marque('C')}", taille=9, couleur=TEXTE_2)
    lignes = []
    for p in pieces:
        siens = [e for e in emetteurs if _champ(e, "piece_id") == _champ(p, "id")]
        def emetteur(e):
            n = _champ(e, "nombre") or 1
            nom = _EMETTEURS.get(_champ(e, "type"), (_champ(e, "type"),) * 2)[0 if n == 1 else 1]
            puissance = _champ(e, "puissance_w")
            detail = f" ({_nombre(puissance, 'W')}{' chacun' if n > 1 else ''})" if puissance else ""
            return f"{n} {nom}{detail}"

        em = ", ".join(emetteur(e) for e in siens) or (
            "Aucun émetteur indiqué" if _champ(p, "chauffee") is not False else "")
        details = [_PIECES.get(_champ(p, "type"), ""), _nombre(_champ(p, "surface_m2"), "m²")]
        if _champ(p, "orientation"):
            details.append(_ORIENTATIONS.get(_champ(p, "orientation"), ""))
        if _champ(p, "chauffee") is False:
            details.append("non chauffée")
        lignes.append([f"{_txt(_champ(p, 'nom'))} {_marque('D')}", ", ".join(x for x in details if x), em])
    _tableau(pdf, ["Pièce", "Détails", "Émetteurs"], [40, 55, 85], lignes)


def _travaux(pdf, travaux):
    if not travaux:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    lignes = []
    for t in travaux:
        justifie = bool(_champ(t, "facture_document_id") or _champ(t, "attestation_assurance_document_id"))
        reception = _champ(t, "date_reception")
        garanties = "; ".join(f"{g['libelle']} jusqu'au {_date(g['fin'])} ({_GARANTIES.get(g['statut'], '')})"
                              for g in (_champ(t, "garanties") or []))
        lignes.append([
            f"{_txt(_champ(t, 'nature'))} {_marque('J' if justifie else 'D')}",
            _CATEGORIES_CIL.get(_champ(t, "categorie_cil"), ""),
            _txt(_champ(t, "entreprise")),
            f"{_date(reception)} {_marque('D')}" if reception else "à indiquer",
            f"{garanties} {_marque('C')}" if garanties else "",
        ])
    _tableau(pdf, ["Chantier", "Catégorie", "Entreprise", "Réception", "Garanties"], [38, 28, 28, 22, 64], lignes)
    _para(pdf, MENTION_GARANTIES, taille=8, style="I", couleur=TEXTE_2)
    for t in travaux:
        description = _champ(t, "note")
        isolants = _champ(t, "isolants") or []
        if not description and not isolants:
            continue
        _place(pdf, 24)
        _sous_titre(pdf, _txt(_champ(t, "nature")))
        if description:
            _para(pdf, f"{_txt(description)} {_marque('D')}", taille=9)
        if isolants:
            _tableau(pdf, ["Isolant", "Marque, référence", "R (m².K/W)", "Lambda (W/m.K)", "Épaisseur", "Surface",
                           "Interfaces"], [28, 32, 18, 18, 20, 18, 46], [
                [f"{_txt(_champ(i, 'nature'))} {_marque('D')}", _txt(_champ(i, "marque_reference")),
                 _nombre(_champ(i, "resistance_thermique")), _nombre(_champ(i, "conductivite"), decimales=3),  # 0,040 W/m.K
                 _nombre(_champ(i, "epaisseur_mm"), "mm"), _nombre(_champ(i, "surface_m2"), "m²"),
                 _txt(_champ(i, "interfaces"))]
                for i in isolants])


def _entretien(pdf, echeances, journal, noms_equipements, aujourd_hui: date):
    if not echeances and not journal:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    if echeances:
        _sous_titre(pdf, "Prochaines échéances")
        _tableau(pdf, ["Tâche", "Pour", "Échéance", "Statut", "Nature", "Qui"], [54, 31, 27, 22, 18, 28], [
            [_txt(e["libelle"]), noms_equipements.get(e["equipement_id"], "La maison"),
             f"{_date(e['echeance'])} {_marque('S' if e.get('reference_supposee') else 'C')}" if e["echeance"] else "",
             _ECHEANCES.get(e["statut"], e["statut"]),
             "obligation" if e["nature"] == "obligation" else "conseil", _QUI.get(e["qui"], e["qui"])]
            for e in echeances])
    limite = date(aujourd_hui.year - MOIS_JOURNAL // 12, aujourd_hui.month, min(aujourd_hui.day, 28))
    retenues = [l for l in journal if l["date"] and (l["date"] >= limite or l["justifie"])]
    _sous_titre(pdf, "Journal (24 derniers mois, et toute entrée justifiée plus ancienne)")
    if not retenues:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    _tableau(pdf, ["Date", "Type", "Ce qui a été fait", "Équipement", "Par", "Coût TTC"], [20, 27, 49, 32, 30, 22], [
        [_date(l["date"]), _JOURNAL.get(l["type"], l["type"]),
         f"{_txt(l['titre'])} {_marque('J' if l['justifie'] else 'D')}",
         noms_equipements.get(l.get("equipement_id"), ""),
         "moi" if l.get("intervenant") == "moi" else _txt(l.get("intervenant")),
         _nombre(l.get("cout_eur"), "€")]
        for l in retenues], aligns=["LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"])


def _energie(pdf, h):
    type_ = _champ(h, "conso_autre_energie_type")
    autre = _FICHE["conso_autre_energie_type"].get(type_, type_ or "")
    if autre and _champ(h, "conso_autre_energie_qte"):
        unite = _FICHE["conso_autre_energie_unite"].get(_champ(h, "conso_autre_energie_unite"))
        autre = f"{autre} : {_nombre(_champ(h, 'conso_autre_energie_qte'), f'{unite}/an' if unite else '')}"
    _fiche(pdf, [
        ("Consommation d'électricité", _nombre(_champ(h, "conso_elec_kwh_an"), "kWh/an"), "D"),
        ("Autre énergie", autre, "D"),
        ("Puissance souscrite", f"{_champ(h, 'puissance_souscrite')} kVA" if _champ(h, "puissance_souscrite") else "", "D"),
        ("Option tarifaire", _FICHE["option_tarifaire"].get(_champ(h, "option_tarifaire"), ""), "D"),
    ])


def _documents(pdf, documents):
    if not documents:
        _para(pdf, NON_RENSEIGNE, couleur=TEXTE_2)
        return
    plans = [d for d in documents if _champ(d, "type") == "plan"]
    autres = [d for d in documents if _champ(d, "type") != "plan"]
    if plans:
        _sous_titre(pdf, "Plans, coupes et schémas de réseaux")
        _tableau(pdf, ["Plan", "Ajouté le"], [120, 60],
                 [[_txt(_champ(d, "filename")), _date(_champ(d, "uploaded_at"))] for d in plans])
    if autres:
        if plans:
            _sous_titre(pdf, "Autres documents")
        _tableau(pdf, ["Type", "Ajouté le"], [60, 120],
                 [[_DOCUMENTS.get(_champ(d, "type"), _champ(d, "type")), _date(_champ(d, "uploaded_at"))] for d in autres])
    _para(pdf, "Les documents restent dans Hélios : ils ne sont pas joints à ce dossier.", taille=8, style="I",
          couleur=TEXTE_2)


# --- Le document --------------------------------------------------------------------------

def dossier_pdf(*, house, equipements=(), travaux=(), pieces=(), emetteurs=(), resume=None, echeances=(),
                journal=(), documents=(), sections=SECTIONS, numeros_serie: bool = False,
                aujourd_hui: date | None = None, fonts_dir: Path = FONTS_DIR) -> bytes:
    """Le PDF, en mémoire. `equipements` portent leur âge (`garanties.age_ans`), `travaux` leurs
    garanties (`garanties.fin_garanties_chantier` + statut), `journal` vient de `journal_fusionne`
    — tout est calculé AVANT ; ce module ne fait que présenter."""
    aujourd_hui = aujourd_hui or date.today()
    pdf = _DossierPDF(fonts_dir, aujourd_hui)
    pdf.set_title("Dossier de la maison")
    pdf.add_page()
    _titre_page(pdf, "Dossier de la maison",
                f"Code postal {_champ(house, 'code_postal')} · généré le {_date(aujourd_hui)}")
    pdf.set_fill_color(*SABLE)
    pdf.police("sans", "", 8)
    pdf.set_text_color(*TEXTE_2)
    pdf.multi_cell(_largeur(pdf), 4, LEGENDE, fill=True, padding=2.5, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*INK)
    pdf.ln(2)

    noms = {_champ(e, "id"): _TYPES.get(_champ(e, "type"), _champ(e, "type")) for e in equipements}
    dpe_justifie = any(_champ(d, "type") == "dpe" for d in documents)
    rendus = {
        "logement": lambda: _logement(pdf, house),
        "enveloppe": lambda: _enveloppe(pdf, house, dpe_justifie),
        "equipements": lambda: _equipements(pdf, list(equipements), numeros_serie),
        "pieces": lambda: _pieces(pdf, list(pieces), list(emetteurs), resume),
        "travaux": lambda: _travaux(pdf, list(travaux)),
        "entretien": lambda: _entretien(pdf, list(echeances), list(journal), noms, aujourd_hui),
        "energie": lambda: _energie(pdf, house),
        "documents": lambda: _documents(pdf, list(documents)),
    }
    for code in SECTIONS:  # l'ordre du document est fixe, quel que soit celui de la demande
        if code in sections:
            _place(pdf, 36)  # le titre de section part avec le début de son contenu
            _section(pdf, TITRES[code])
            rendus[code]()
    return bytes(pdf.output())
