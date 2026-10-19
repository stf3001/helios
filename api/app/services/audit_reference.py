"""Tables de référence du pré-audit — doc 07 §6 (méthode 3CL simplifiée dégradée), moteur v2.

ATTENTION : ce sont des ORDRES DE GRANDEUR (France 2026) destinés à un pré-diagnostic
indicatif, PAS un DPE réglementaire. Toutes ces valeurs sont calibrables ici (ou dans
`config.py`, sous `audit_*`) et doivent rester cohérentes avec les chunks `verif` de la base
de connaissances (doc 07 §6.4). Les chiffres ne sont JAMAIS produits par le LLM.

Chaque table indexée par une valeur de la fiche couvre TOUTES les valeurs `Literal` de
`schemas/house.py` — `tests/test_audit_engine.py` le vérifie. Une valeur absente de la fiche
(None) est traitée explicitement par le moteur comme « inconnue → hypothèse », jamais par
un repli silencieux.
"""

# Valeur CENTRALE de chaque classe DPE, en kWh d'énergie PRIMAIRE par m² et par an, TOUS
# USAGES (chauffage, eau chaude, refroidissement, éclairage, auxiliaires) — pas un besoin
# de chauffage. Seuils de classe : A <= 70, B <= 110, C <= 180, D <= 250, E <= 330,
# F <= 420, G > 420. Milieu de classe de B à F ; A et G sont ouvertes, d'où une convention :
# 50 pour A (une maison existante descend rarement plus bas), 480 pour G (A CALIBRER).
# La lettre peut être tirée par le seuil GES (double étiquette) : la valeur est approchée.
DPE_KWH_EP_M2_AN: dict[str, int] = {
    "A": 50, "B": 90, "C": 145, "D": 215, "E": 290, "F": 375, "G": 480,
}

# Sans DPE : BESOIN DE CHAUFFAGE UTILE (chaleur à fournir, avant rendement du système), en
# kWh/m²/an, maison de référence en zone H1. Ordres de grandeur A CALIBRER PAR STÉPHANE.
# Les clés sont exactement celles d'`AnneeConstruction`.
ANNEE_BESOIN_UTILE_KWH_M2_AN: dict[str, int] = {
    "avant_1948": 220,
    "1948_1974": 240,
    "1975_1988": 180,
    "1989_2000": 130,
    "2001_2012": 100,
    "apres_2012": 50,
}
# Année inconnue : le parc ancien est majoritaire, on suppose 1948-1974 (hypothèse affichée).
ANNEE_DEFAUT = "1948_1974"

# Énergie consommée par chaque système de chauffage. « autre » n'est pas qualifié par la
# fiche : on le traite comme de l'électricité, et c'est écrit dans les hypothèses.
ENERGIE_CHAUFFAGE: dict[str, str] = {
    "elec_direct": "electricite",
    "PAC_air_eau": "electricite",
    "PAC_air_air": "electricite",
    "gaz": "gaz",
    "fioul": "fioul",
    "bois": "bois",
    "reseau": "reseau",
    "autre": "electricite",
}
# Chauffage inconnu : le cas le plus fréquent d'une maison française, convecteurs électriques.
CHAUFFAGE_DEFAUT = "elec_direct"

# Zone climatique par département (France métropolitaine, Corse comprise).
# Source : arrêté du 26 octobre 2010 (RT 2012), annexe I « zones climatiques », et la
# « répartition des départements par zone climatique » publiée par le ministère de la
# Transition écologique (ecologie.gouv.fr). Les sous-zones (H1a/b/c, H2a/b/c/d) sont
# regroupées : le moteur n'utilise que H1/H2/H3. Découpage administratif, pas un réglage.
_ZONES: dict[str, tuple[str, ...]] = {
    # H1a, H1b, H1c
    "H1": ("02", "14", "27", "50", "59", "60", "61", "62", "75", "76", "77", "78", "80", "91",
           "92", "93", "94", "95",
           "08", "10", "45", "51", "52", "54", "55", "57", "58", "67", "68", "70", "88", "89", "90",
           "01", "03", "05", "15", "19", "21", "23", "25", "38", "39", "42", "43", "63", "69",
           "71", "73", "74", "87"),
    # H2a, H2b, H2c, H2d
    "H2": ("22", "29", "35", "56",
           "16", "17", "18", "28", "36", "37", "41", "44", "49", "53", "72", "79", "85", "86",
           "09", "12", "24", "31", "32", "33", "40", "46", "47", "64", "65", "81", "82",
           "04", "07", "26", "48", "84"),
    "H3": ("06", "11", "13", "2A", "2B", "30", "34", "66", "83"),
}
ZONE_CLIMATIQUE: dict[str, str] = {dep: zone for zone, deps in _ZONES.items() for dep in deps}

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
PONTS_THERMIQUES_COEF = 0.7  # non renseignable dans la fiche — hypothèse fixe

# Coefficient de déperdition résiduelle par qualité d'isolation d'un poste (1.0 = non isolé).
# Il module aussi le gain de l'action correspondante : isoler un poste à moitié isolé
# rapporte moins que d'isoler un poste nu.
QUALITE_ISOLATION: dict[str, float] = {
    "aucune": 1.0,
    "partielle": 0.6,
    "bonne": 0.3,
    "inconnue": 0.85,   # prudence : on suppose plutôt mal isolé
}
QUALITE_MENUISERIES: dict[str, float] = {
    "simple": 1.0,
    "double": 0.5,
    "double_recent": 0.4,
    "triple": 0.3,
    "inconnue": 0.7,    # valeur pour un champ non renseigné (pas une option du formulaire)
}
QUALITE_VENTILATION: dict[str, float] = {
    "aucune": 1.0,           # infiltrations non maîtrisées
    "naturelle": 0.9,
    "VMC_simple": 0.7,
    "VMC_double": 0.4,       # récupération de chaleur
    "inconnue": 0.85,
}

# Quand une action est proposée, poste par poste (une entrée par valeur du schéma).
ISOLATION_A_TRAITER: dict[str, bool] = {"aucune": True, "partielle": True, "bonne": False, "inconnue": True}
MENUISERIES_A_REMPLACER: dict[str, bool] = {
    "simple": True, "double": False, "double_recent": False, "triple": False, "inconnue": True,
}
VENTILATION_A_REMPLACER: dict[str, bool] = {
    "aucune": True, "naturelle": True, "VMC_simple": False, "VMC_double": False, "inconnue": False,
}
REGULATION_A_AMELIORER: dict[str, bool] = {
    "aucune": True, "thermostat": False, "programmable": False, "connecte": False,
}
# Systèmes à remplacer en priorité par une PAC (valeurs exactes du schéma `Chauffage`).
CHAUFFAGE_A_REMPLACER = {"elec_direct", "gaz", "fioul"}

# Actions de rénovation recommandables. Coûts TTC pose comprise, ordres de grandeur 2026.
# `unit` : "m2_emprise" (surface habitable / nombre de niveaux : combles, plancher bas),
#          "m2_mur" (surface de murs estimée), "fenetre", "forfait".
# `aide_pct_bas` / `aide_pct_haut` : part prise en charge (MaPrimeRénov' + CEE), des revenus
#   élevés aux revenus modestes. Le haut reprend la valeur v1 ; le bas ~ CEE seuls.
#   A VÉRIFIER (cf. `audit_aides_date_reference`).
# `gain_pct_chauffage` : économie sur la CONSO DE CHAUFFAGE quand le poste est nu, modulée
#   ensuite par son état (QUALITE_*). A CALIBRER.
# `duree_vie_ans` : au-delà, un temps de retour n'a plus de sens. A CALIBRER.
# `libelle_occasion` : quand faire l'action si elle ne se justifie pas seule.
ACTIONS: dict[str, dict] = {
    "isolation_combles": {
        "poste": "toiture",
        "label": "Isolation des combles / toiture",
        "cout_bas": 25, "cout_haut": 70, "unit": "m2_emprise",
        "aide_pct_bas": 0.15, "aide_pct_haut": 0.45,
        "gain_pct_chauffage": 0.25,
        "duree_vie_ans": 30,
        "libelle_occasion": "lors d'une réfection de la toiture ou de l'aménagement des combles",
        "priorite_hierarchie": 2,  # enveloppe
    },
    "isolation_murs": {
        "poste": "murs",
        "label": "Isolation des murs",
        "cout_bas": 90, "cout_haut": 180, "unit": "m2_mur",
        # NB : la base de connaissances (`kb/baremes_aides.md`) indique que l'isolation des
        # murs SEULE n'est plus aidée par MaPrimeRénov' par geste depuis le 01/01/2026.
        "aide_pct_bas": 0.10, "aide_pct_haut": 0.40,
        "gain_pct_chauffage": 0.20,
        "duree_vie_ans": 40,
        "libelle_occasion": "lors d'un ravalement de façade",
        "priorite_hierarchie": 2,
    },
    "isolation_plancher": {
        "poste": "plancher",
        "label": "Isolation du plancher bas",
        "cout_bas": 30, "cout_haut": 60, "unit": "m2_emprise",
        "aide_pct_bas": 0.15, "aide_pct_haut": 0.35,
        "gain_pct_chauffage": 0.08,
        "duree_vie_ans": 40,
        "libelle_occasion": "lors d'une réfection des sols ou si le vide sanitaire est accessible",
        "priorite_hierarchie": 2,
    },
    "menuiseries": {
        "poste": "menuiseries",
        "label": "Remplacement des menuiseries (double/triple vitrage)",
        "cout_bas": 500, "cout_haut": 800, "unit": "fenetre",
        "aide_pct_bas": 0.05, "aide_pct_haut": 0.25,
        "gain_pct_chauffage": 0.12,
        "duree_vie_ans": 30,
        "libelle_occasion": "au remplacement des fenêtres en fin de vie",
        "priorite_hierarchie": 2,
    },
    "ventilation_double_flux": {
        "poste": "air_ventilation",
        "label": "Ventilation VMC double flux",
        "cout_bas": 4000, "cout_haut": 7000, "unit": "forfait",
        "aide_pct_bas": 0.10, "aide_pct_haut": 0.30,
        "gain_pct_chauffage": 0.12,
        "duree_vie_ans": 20,
        "libelle_occasion": "lors d'une rénovation globale, une fois l'enveloppe étanche",
        "priorite_hierarchie": 3,  # systèmes
    },
    "pac_air_eau": {
        "poste": "systeme_chauffage",
        "label": "Pompe à chaleur air/eau (remplacement du chauffage actuel)",
        "cout_bas": 12000, "cout_haut": 18000, "unit": "forfait",
        "aide_pct_bas": 0.15, "aide_pct_haut": 0.40,
        # Pas de pourcentage : l'économie se calcule par changement d'énergie (moteur).
        "duree_vie_ans": 17,
        "libelle_occasion": "au remplacement du système actuel en fin de vie",
        "priorite_hierarchie": 3,
    },
    "regulation": {
        "poste": "pilotage",
        "label": "Thermostat programmable / régulation",
        "cout_bas": 150, "cout_haut": 500, "unit": "forfait",
        "aide_pct_bas": 0.0, "aide_pct_haut": 0.0,
        "gain_pct_chauffage": 0.10,
        "duree_vie_ans": 10,
        "libelle_occasion": "au prochain remplacement du thermostat",
        "priorite_hierarchie": 1,  # sobriété (geste peu coûteux, esprit colibri)
    },
}

# Estimation grossière du nombre de fenêtres à partir de la surface habitable (1 fenêtre / ~15 m²).
M2_PAR_FENETRE = 15

# Ordre d'affichage des horizons.
HORIZONS = ("maintenant", "prioritaire", "a_l_occasion")

# Provenance des valeurs de référence, reprise dans le bloc `hypotheses` du pré-audit.
SOURCES: dict[str, tuple[str, str]] = {
    "dpe_kwh_ep_m2_an": ("Milieu de classe DPE (seuils arrêté du 31/03/2021)", "2026-10-19"),
    "besoin_utile_kwh_m2_an": ("Ordre de grandeur par année de construction, à calibrer", "2026-10-19"),
    "coef_ep_ef": ("Coefficient de conversion énergie primaire / finale", "2026-01-01"),
    "part_chauffage_dpe": ("Part du chauffage dans le DPE tous usages, à calibrer", "2026-10-19"),
    "rendement_chauffage": ("Rendement saisonnier, ordre de grandeur", "2026-10-19"),
    "zone_climatique": ("Arrêté du 26/10/2010, annexe I", "2010-10-26"),
    "coef_zone": ("Correction climatique H1/H2/H3, à calibrer (altitude ignorée)", "2026-10-19"),
    "prix_electricite": ("TRV option Base (simulateur)", "2026-08-01"),
    "prix_gaz": ("Prix repère CRE, usage chauffage", "2026-10-01"),
    "prix_fioul": ("Moyenne DGEC, 1,88 €/L / 10 kWh", "2026-09-30"),
    "prix_bois": ("Entre bûches et granulés, à valider", "2026-10-19"),
    "prix_reseau": ("Prix moyen réseau de chaleur", "2026-03-01"),
    "usages_specifiques": ("Couches de consommation du simulateur (simu_conso_*)", "2026-10-19"),
    "deperditions": ("Répartition ADEME d'une maison non isolée, modulée", "2026-07-18"),
    "couts_actions": ("Ordres de grandeur TTC posés, à calibrer", "2026-07-18"),
    "aides": ("MaPrimeRénov' + CEE, fourchette à vérifier", "2026-07-18"),
    "gains_actions": ("Gain sur le chauffage par action, à calibrer", "2026-10-19"),
    "horizons": ("Seuils de classement, à confirmer", "2026-10-19"),
    "ratio_murs": ("Surface de murs / surface habitable, à calibrer", "2026-10-19"),
    "incertitude": ("Demi-largeur des fourchettes", "2026-07-18"),
}
