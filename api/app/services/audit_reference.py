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
# `aide` : fourchette du revenu le plus élevé (bas) au plus modeste (haut), de trois formes :
#   ("pct", bas, haut)    part du coût central — valeurs v1, A VÉRIFIER ;
#   ("eur_m2", bas, haut) euros par m² traité ; ("eur", bas, haut) forfait en euros.
#   `aide_source` renvoie à la fiche de `kb/baremes_aides.md` (relevé du 22/07/2026, mis à
#   jour le 20/10/2026 pour la réforme du 1er septembre 2026, décret n° 2026-822) quand elle
#   existe ; sans elle, l'aide est affichée « à vérifier ». `aide_note` s'affiche avec.
# `gain_pct_chauffage` : économie sur la CONSO DE CHAUFFAGE quand le poste est nu, modulée
#   ensuite par son état (QUALITE_*). A CALIBRER.
# `duree_vie_ans` : au-delà, un temps de retour n'a plus de sens. A CALIBRER.
# `libelle_occasion` : quand faire l'action si elle ne se justifie pas seule.
ACTIONS: dict[str, dict] = {
    "isolation_combles": {
        "poste": "toiture",
        "label": "Isolation des combles / toiture",
        "cout_bas": 25, "cout_haut": 70, "unit": "m2_emprise",
        # kb/baremes_aides.md, « Quel montant MaPrimeRénov' pour l'isolation des combles ou de
        # la toiture en 2026 ? » : sortie du parcours par geste pour tout dossier déposé depuis
        # le 01/09/2026 (décret n° 2026-822). Les CEE restent, sans barème national.
        "aide": ("eur_m2", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("plus aidée par MaPrimeRénov' par geste depuis le 01/09/2026 ; primes CEE "
                      "possibles (montant variable) ; finançable en rénovation d'ampleur"),
        "gain_pct_chauffage": 0.25,
        "duree_vie_ans": 30,
        "libelle_occasion": "lors d'une réfection de la toiture ou de l'aménagement des combles",
        "priorite_hierarchie": 2,  # enveloppe
    },
    "isolation_murs": {
        "poste": "murs",
        "label": "Isolation des murs",
        "cout_bas": 90, "cout_haut": 180, "unit": "m2_mur",
        # kb/baremes_aides.md, « Peut-on encore isoler ses murs avec MaPrimeRénov' en 2026 ? » :
        # plus aidée par geste depuis le 01/01/2026 (décret du 08/09/2025).
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("finançable uniquement en rénovation d'ampleur (bouquet de travaux visant au "
                      "moins 2 classes de DPE, accompagnateur agréé)"),
        "gain_pct_chauffage": 0.20,
        "duree_vie_ans": 40,
        "libelle_occasion": "lors d'un ravalement de façade",
        "priorite_hierarchie": 2,
    },
    "isolation_plancher": {
        "poste": "plancher",
        "label": "Isolation du plancher bas",
        "cout_bas": 30, "cout_haut": 60, "unit": "m2_emprise",
        # Plus aidée par geste depuis le 01/01/2026, comme les murs.
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("plus aidée par MaPrimeRénov' par geste depuis le 01/01/2026 ; primes CEE "
                      "possibles ; finançable en rénovation d'ampleur"),
        "gain_pct_chauffage": 0.08,
        "duree_vie_ans": 40,
        "libelle_occasion": "lors d'une réfection des sols ou si le vide sanitaire est accessible",
        "priorite_hierarchie": 2,
    },
    "menuiseries": {
        "poste": "menuiseries",
        "label": "Remplacement des menuiseries (double/triple vitrage)",
        "cout_bas": 500, "cout_haut": 800, "unit": "fenetre",
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("plus aidées par MaPrimeRénov' par geste depuis le 01/09/2026 ; primes CEE "
                      "possibles ; finançables en rénovation d'ampleur"),
        "gain_pct_chauffage": 0.12,
        "duree_vie_ans": 30,
        "libelle_occasion": "au remplacement des fenêtres en fin de vie",
        "priorite_hierarchie": 2,
    },
    "ventilation_double_flux": {
        "poste": "air_ventilation",
        "label": "Ventilation VMC double flux",
        "cout_bas": 4000, "cout_haut": 7000, "unit": "forfait",
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("plus aidée par MaPrimeRénov' par geste depuis le 01/09/2026 ; primes CEE "
                      "possibles ; finançable en rénovation d'ampleur"),
        "gain_pct_chauffage": 0.12,
        "duree_vie_ans": 20,
        "libelle_occasion": "lors d'une rénovation globale, une fois l'enveloppe étanche",
        "priorite_hierarchie": 3,  # systèmes
    },
    "pac_air_eau": {
        "poste": "systeme_chauffage",
        "label": "Pompe à chaleur air/eau (remplacement du chauffage actuel)",
        "cout_bas": 12000, "cout_haut": 18000, "unit": "forfait",
        # kb/baremes_aides.md, « Quel montant MaPrimeRénov' pour une pompe à chaleur en 2026 ? » :
        # air/eau ~5 000 / 4 000 / 3 000 € (très modeste / modeste / intermédiaire), 0 au-delà.
        "aide": ("eur", 0, 5000),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("+ CEE possibles, montant variable selon le fournisseur ; le projet de loi de "
                      "finances 2027 pourrait modifier cette aide"),
        # Pas de pourcentage : l'économie se calcule par changement d'énergie (moteur).
        "duree_vie_ans": 17,
        "libelle_occasion": "au remplacement du système actuel en fin de vie",
        "priorite_hierarchie": 3,
    },
    "regulation": {
        "poste": "pilotage",
        "label": "Thermostat programmable / régulation",
        "cout_bas": 150, "cout_haut": 500, "unit": "forfait",
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": "primes CEE possibles pour une régulation posée par un professionnel",
        "gain_pct_chauffage": 0.10,
        "duree_vie_ans": 10,
        "libelle_occasion": "au prochain remplacement du thermostat",
        "priorite_hierarchie": 1,  # sobriété (geste peu coûteux, esprit colibri)
    },
    # Eau chaude, pas chauffage : son économie ne se combine pas avec celles du chauffage.
    # Coûts dans `config.audit_ballon_thermo_*` (complet, ou surcoût si l'ancien est en fin
    # de vie) ; économie = écart des couches ECS du simulateur x occupants x prix élec.
    "ballon_thermodynamique": {
        "poste": "eau_chaude",
        "label": "Ballon d'eau chaude thermodynamique",
        "unit": "forfait",
        "aide": ("eur", 0, 0),
        "aide_source": "kb/baremes_aides.md (20/10/2026)",
        "aide_note": ("plus aidé par MaPrimeRénov' par geste depuis le 01/09/2026 ; primes CEE "
                      "possibles (montant variable)"),
        "duree_vie_ans": 15,
        "libelle_occasion": "au remplacement du ballon",
        "libelle_fin_de_vie": "au remplacement de votre ballon, qui approche de sa fin de vie",
        "priorite_hierarchie": 3,
    },
}

# Ligne « production solaire » : chiffres CITÉS d'une étude du simulateur, jamais recalculés.
SOLAIRE = {
    "action": "production_solaire",
    "label": "Production solaire (d'après votre étude du simulateur)",
    "poste": "production",
    "priorite_hierarchie": 4,  # production, après sobriété, enveloppe et systèmes
    "duree_vie_ans": 25,       # durée d'étude du simulateur (`simu_duree_etude_ans`)
    "libelle_occasion": "lors d'une réfection de la toiture, ou quand le projet se précise",
}
PISTE_SOLAIRE = (
    "Votre maison consomme {conso} kWh d'électricité par an : une production solaire pourrait "
    "en couvrir une partie. Estimez-la avec le simulateur (pré-rempli avec votre fiche)."
)
PISTE_SOLAIRE_COURTE = "Estimer votre production solaire avec le simulateur"
LIEN_SIMULATEUR = "/simulateur-solaire"

# Postes d'isolation : s'il y en a et qu'aucun n'est rentable, l'audit le dit.
POSTES_ISOLATION = {"isolation_combles", "isolation_murs", "isolation_plancher", "menuiseries"}
MESSAGE_SANS_ISOLATION = (
    "Aucune isolation n'est rentable à court terme : votre chauffage vous coûte environ "
    "{cout} €/an. Les leviers utiles sont ailleurs : {leviers}."
)

# Équipements dont l'âge est surveillé (clés de `audit_duree_vie_*`).
# (nom, pronom) : « faites-la entretenir » pour une pompe, « faites-le » pour un ballon.
NOM_EQUIPEMENT: dict[str, tuple[str, str]] = {
    "PAC_air_air": ("pompe à chaleur air/air", "la"),
    "PAC_air_eau": ("pompe à chaleur air/eau", "la"),
    "gaz": ("chaudière gaz", "la"),
    "fioul": ("chaudière fioul", "la"),
    "ballon_elec": ("ballon d'eau chaude électrique", "le"),
    "thermodynamique": ("ballon thermodynamique", "le"),
}
CONSEIL_AGE = ("Votre {equipement} a {age} ans : faites-{pronom} entretenir et préparez son "
               "remplacement plutôt que de le subir en panne.")
CONSEIL_AGE_PAC = " Au remplacement, une PAC récente consomme généralement moins."

# Appoint qui ne passe pas (ou pas forcément) par le compteur électrique.
APPOINT_HORS_FACTURE = {"autre", "bois", "gaz", "fioul", "reseau"}

# Gestes gratuits, horizon « maintenant ». Des CONSEILS, sans chiffre d'économie, hors
# synthèse financière. `si_chauffage` : None = toujours, sinon les systèmes concernés.
GESTES_GRATUITS: tuple[dict, ...] = (
    {"cle": "consigne_19", "texte": "Réglez la consigne à 19 °C dans les pièces de vie, moins "
                                     "dans les chambres et la nuit.", "si_chauffage": None},
    {"cle": "programmation", "texte": "Programmez le chauffage selon votre présence : il baisse "
                                       "quand la maison est vide.", "si_chauffage": None},
    {"cle": "filtres_pac", "texte": "Nettoyez régulièrement les filtres de la pompe à chaleur et "
                                     "faites-la entretenir.", "si_chauffage": {"PAC_air_air", "PAC_air_eau"}},
    {"cle": "entretien_chaudiere", "texte": "Faites entretenir la chaudière chaque année (obligatoire).",
     "si_chauffage": {"gaz", "fioul", "bois"}},
    {"cle": "volets_nuit", "texte": "Fermez volets et rideaux la nuit en hiver.", "si_chauffage": None},
)

# Confort d'été, zones H2 et H3 : qualitatif, sans chiffre.
ZONES_CONFORT_ETE = {"H2", "H3"}
CONFORT_ETE: tuple[str, ...] = (
    "Des protections solaires extérieures (volets, stores, brise-soleil) sur les baies exposées "
    "sud et ouest : elles arrêtent la chaleur avant qu'elle n'entre.",
    "Ventiler la nuit, quand l'air extérieur est plus frais, et fermer en journée.",
    "Des brasseurs d'air (ventilateurs de plafond) avant toute climatisation supplémentaire.",
    "L'isolation des combles, qui limite fortement la chaleur sous le toit.",
)
CONFORT_ETE_COMBLES = ("Peu rentable sur votre chauffage, l'isolation des combles reste le premier "
                       "levier contre la surchauffe d'été.")

# Estimation grossière du nombre de fenêtres à partir de la surface habitable (1 fenêtre / ~15 m²).
M2_PAR_FENETRE = 15

# Libellés en français des valeurs de la fiche (`schemas/house.py`), pour le document.
# Une valeur absente d'une table s'affiche telle quelle : jamais d'erreur à l'affichage.
LIBELLE_VALEUR: dict[str, dict[str, str]] = {
    "type_logement": {"maison": "Maison", "appartement": "Appartement"},
    "chauffage_principal": {
        "elec_direct": "convecteurs électriques", "PAC_air_eau": "pompe à chaleur air/eau",
        "PAC_air_air": "pompe à chaleur air/air", "gaz": "chaudière gaz", "fioul": "chaudière fioul",
        "bois": "chauffage au bois", "reseau": "réseau de chaleur", "autre": "autre chauffage",
    },
    "ecs": {
        "ballon_elec": "ballon électrique", "thermodynamique": "ballon thermodynamique",
        "gaz": "chaudière gaz", "solaire": "chauffe-eau solaire", "instantane": "chauffe-eau instantané",
    },
    "zone_climatique": {"H1": "climat froid", "H2": "climat tempéré", "H3": "climat doux"},
}
LIBELLE_VALEUR["chauffage_appoint"] = LIBELLE_VALEUR["chauffage_principal"]

# « Pour un pré-audit plus précis » : les valeurs SUPPOSÉES de la fiche, du plus au moins
# décisif pour le résultat. Le moteur en retient les 3 premières. Chaque entrée : (champ,
# libellé, ce que le moteur a supposé à la place). L'hypothèse peut citer un réglage :
# `{kva}`, `{occupants}`.
#  - surface et chauffage d'abord : sans eux, rien n'est chiffré juste (un chauffage
#    inconnu est traité en convecteurs, l'énergie la plus chère) ;
#  - la facture ensuite : c'est elle qui cale toutes les économies sur le réel ;
#  - puis ce qui fixe l'estimation (DPE, année), l'état de l'enveloppe, l'âge des
#    équipements (qui décide « surcoût » ou « coût complet »), et le reste.
CHAMPS_A_PRECISER: tuple[tuple[str, str, str], ...] = (
    ("surface_habitable", "Votre surface habitable", "inconnue : rien n'est chiffré au m²"),
    ("chauffage_principal", "Votre chauffage principal", "supposé : convecteurs électriques"),
    ("conso_elec_kwh_an", "Votre consommation d'électricité (facture)",
     "inconnue : économies calculées sur une estimation"),
    ("dpe_lettre", "La lettre de votre DPE", "inconnue : estimation d'après l'année de construction"),
    ("annee_construction", "L'année de construction", "inconnue : une maison de 1948-1974 est supposée"),
    ("isolation_combles", "L'isolation de vos combles", "inconnue : supposée faible"),
    ("isolation_murs", "L'isolation de vos murs", "inconnue : supposée faible"),
    ("isolation_plancher", "L'isolation de votre plancher bas", "inconnue : supposée faible"),
    ("menuiseries", "Vos fenêtres", "inconnues : supposées anciennes"),
    ("chauffage_principal_annee", "L'année de votre chauffage", "inconnue : son âge n'est pas évalué"),
    ("ecs", "Votre production d'eau chaude", "supposée : ballon électrique"),
    ("ecs_annee", "L'année de votre ballon d'eau chaude",
     "inconnue : le ballon thermodynamique est chiffré au prix complet"),
    ("nb_occupants", "Le nombre d'occupants", "supposé : {occupants} personnes"),
    ("puissance_souscrite", "Votre puissance souscrite", "supposée : {kva} kVA"),
    ("nb_niveaux", "Le nombre de niveaux", "supposé : 1 niveau"),
)
A_PRECISER_MAX = 3
# Avec un DPE déclaré, l'année de construction n'entre pas dans l'estimation : on ne
# prétend pas l'avoir supposée.
ANNEE_AVEC_DPE = "inconnue : l'estimation repose sur la lettre de votre DPE"

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
    "aides": ("kb/baremes_aides.md quand la fiche existe, sinon à vérifier", "2026-07-22"),
    "equipements": ("Durées de vie typiques, à calibrer", "2026-10-19"),
    "ballon_thermo": ("Coût du ballon thermodynamique, à valider", "2026-10-19"),
    "gains_actions": ("Gain sur le chauffage par action, à calibrer", "2026-10-19"),
    "horizons": ("Seuils de classement, à confirmer", "2026-10-19"),
    "ratio_murs": ("Surface de murs / surface habitable, à calibrer", "2026-10-19"),
    "incertitude": ("Demi-largeur des fourchettes", "2026-07-18"),
}
