"""Tables de référence du pré-audit — doc 07 §6 (méthode 3CL simplifiée dégradée).

ATTENTION : ce sont des ORDRES DE GRANDEUR (France 2026) destinés à un pré-diagnostic
indicatif, PAS un DPE réglementaire. Toutes ces valeurs sont calibrables ici et doivent
rester cohérentes avec les chunks `verif` de la base de connaissances (doc 07 §6.4).
Les chiffres ne sont JAMAIS produits par le LLM — uniquement par ce moteur déterministe.
"""

# Besoin de chauffage de référence par lettre DPE (kWh/m²/an, énergie primaire ~).
# Point d'ancrage prioritaire quand la fiche renseigne le DPE.
DPE_KWH_M2_AN: dict[str, int] = {
    "A": 50, "B": 90, "C": 150, "D": 240, "E": 330, "F": 420, "G": 500,
}

# Besoin estimé à défaut de DPE, par tranche d'année de construction (kWh/m²/an).
# Les libellés doivent matcher les valeurs du champ `annee_construction` de la fiche.
ANNEE_KWH_M2_AN: dict[str, int] = {
    "avant_1948": 330,
    "1948_1974": 350,
    "1975_1988": 280,
    "1989_2000": 210,
    "2001_2012": 130,
    "2013_2020": 90,
    "apres_2021": 60,
}
_DEFAUT_KWH_M2_AN = 280  # tranche inconnue → hypothèse prudente (parc ancien majoritaire)

# Répartition de référence des déperditions d'une maison NON isolée (part du total, ADEME).
# Le moteur module ces parts selon l'état d'isolation réel de chaque poste, puis renormalise.
DEPERDITION_BASE: dict[str, float] = {
    "toiture": 0.28,       # combles / toiture
    "murs": 0.23,
    "air_ventilation": 0.22,
    "menuiseries": 0.13,
    "plancher": 0.09,
    "ponts_thermiques": 0.05,
}

# Coefficient de déperdition résiduelle par qualité d'isolation d'un poste (1.0 = non isolé).
# Plus le poste est isolé, moins il déperd → part réduite.
QUALITE_ISOLATION: dict[str, float] = {
    "aucune": 1.0,
    "partielle": 0.6,
    "bonne": 0.3,
    "inconnue": 0.85,   # prudence : on suppose plutôt mal isolé
    None: 0.85,
}

# Menuiseries → coefficient de déperdition résiduel du poste "menuiseries".
QUALITE_MENUISERIES: dict[str, float] = {
    "simple": 1.0,
    "double": 0.5,
    "double_recent": 0.4,
    "triple": 0.3,
    "inconnue": 0.7,
    None: 0.7,
}

# Ventilation → coefficient de déperdition résiduel du poste "air_ventilation".
QUALITE_VENTILATION: dict[str, float] = {
    "aucune": 1.0,           # infiltrations non maîtrisées
    "naturelle": 0.9,
    "VMC_simple": 0.7,
    "VMC_double": 0.4,       # récupération de chaleur
    "inconnue": 0.85,
    None: 0.85,
}

# Actions de rénovation recommandables : coût (€, fourchette basse/haute) + aide indicative + gain.
# `unit` : "m2_habitable", "m2_mur", "forfait". Coûts TTC pose comprise, ordres de grandeur 2026.
# `aide_pct` : part indicative prise en charge (MaPrimeRénov' + CEE cumulés), À CONFIRMER.
ACTIONS: dict[str, dict] = {
    "isolation_combles": {
        "poste": "toiture",
        "label": "Isolation des combles / toiture",
        "cout_bas": 25, "cout_haut": 70, "unit": "m2_habitable",
        "aide_pct": 0.45,
        "gain_pct_conso": 0.20,
        "priorite_hierarchie": 2,  # enveloppe
    },
    "isolation_murs": {
        "poste": "murs",
        "label": "Isolation des murs",
        "cout_bas": 90, "cout_haut": 180, "unit": "m2_habitable",
        "aide_pct": 0.40,
        "gain_pct_conso": 0.18,
        "priorite_hierarchie": 2,
    },
    "isolation_plancher": {
        "poste": "plancher",
        "label": "Isolation du plancher bas",
        "cout_bas": 30, "cout_haut": 60, "unit": "m2_habitable",
        "aide_pct": 0.35,
        "gain_pct_conso": 0.07,
        "priorite_hierarchie": 2,
    },
    "menuiseries": {
        "poste": "menuiseries",
        "label": "Remplacement des menuiseries (double/triple vitrage)",
        "cout_bas": 500, "cout_haut": 800, "unit": "fenetre",
        "aide_pct": 0.25,
        "gain_pct_conso": 0.10,
        "priorite_hierarchie": 2,
    },
    "ventilation_double_flux": {
        "poste": "air_ventilation",
        "label": "Ventilation VMC double flux",
        "cout_bas": 4000, "cout_haut": 7000, "unit": "forfait",
        "aide_pct": 0.30,
        "gain_pct_conso": 0.10,
        "priorite_hierarchie": 3,  # systèmes
    },
    "pac_air_eau": {
        "poste": "systeme_chauffage",
        "label": "Pompe à chaleur air/eau (remplacement chaudière fioul/gaz)",
        "cout_bas": 12000, "cout_haut": 18000, "unit": "forfait",
        "aide_pct": 0.40,
        "gain_pct_conso": 0.25,
        "priorite_hierarchie": 3,
    },
    "regulation": {
        "poste": "pilotage",
        "label": "Thermostat programmable / régulation",
        "cout_bas": 150, "cout_haut": 500, "unit": "forfait",
        "aide_pct": 0.0,
        "gain_pct_conso": 0.08,
        "priorite_hierarchie": 1,  # sobriété (geste peu coûteux, esprit colibri)
    },
}

# Systèmes de chauffage considérés « à remplacer en priorité » (énergivores / fossiles).
CHAUFFAGE_A_REMPLACER = {"fioul", "gaz", "convecteurs_elec", "electrique"}

# Estimation grossière du nombre de fenêtres à partir de la surface habitable (1 fenêtre / ~15 m²).
M2_PAR_FENETRE = 15
