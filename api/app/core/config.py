from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Le .env vit a la racine du depot (helios/), pas dans api/. On le resout en absolu depuis ce
# fichier : un chemin relatif dependait du dossier de lancement, or l'API demarre depuis api/
# et les agents en ligne de commande depuis helios/ — les deux ne voyaient pas le meme fichier.
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://helios:change-me@localhost:5432/helios"
    jwt_secret: str = "change-me"
    admin_token: str = "change-me-admin"  # secret pour les endpoints admin (validation partenaires)
    llm_api_provider: str = "anthropic"
    llm_api_key: str = ""            # emplacement réservé — clé à venir
    llm_api_model: str = "claude-haiku-4-5-20251001"
    llm_api_budget_daily_eur: float = 5.0
    llm_api_budget_monthly_eur: float = 100.0
    llm_api_daily_requests_per_user: int = 3  # quota "conseils approfondis" par client et par jour
    llm_price_per_1k_tokens_eur: float = 0.005  # estimation grossière (blended in/out) — à calibrer
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    embed_model: str = "bge-m3"
    # Durée de maintien des modèles en RAM par Ollama. Par défaut Ollama les décharge au bout
    # de 5 min : la requête suivante repaie le chargement (~10 s) ET le prefill du prompt
    # (~85 s mesurées sur le poste de dev, la constitution pesant 1 400 des 2 325 tokens).
    # Exprimé en SECONDES (Ollama refuse la chaîne « -1 », qu'il lit comme une durée sans
    # unité) ; -1 = ne jamais décharger. ~3,2 Go de RAM pour les deux modèles, contre ~95 s
    # par requête après une période d'inactivité. Mettre 1800 (30 min) si la RAM est comptée.
    ollama_keep_alive: int = -1
    sobry_partner_link: str = ""

    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30
    email_verify_ttl_hours: int = 48
    frontend_url: str = "http://localhost:5173"
    email_api_key: str = ""  # Resend/Brevo — vide en dev : le lien est loggé au lieu d'être envoyé
    cookie_secure: bool = False  # True en prod (HTTPS) — cf. deploy/

    embed_dimensions: int = 1024  # bge-m3 (doc 10 §1)
    rag_top_k: int = 8
    rag_score_threshold: float = 0.5  # similarité cosinus min. sous laquelle Helios répond en mode prudent
    # Réponse instantanée (doc 07 §5 « cache ») : si une fiche Q/R matche au-delà de ce
    # score, on la sert telle quelle sans LLM (latence ~0). Calibré sur bge-m3 en mesurant
    # la base réelle (20/07/2026) : question exacte 0.69-0.80, paraphrase 0.67-0.69,
    # hors sujet 0.36. Le chunk Q+R dilue les scores, d'où un seuil plus bas qu'intuitif.
    rag_instant_answer_threshold: float = 0.66
    constitution_version: str = "v0.2"  # doit suivre prompts/constitution-<version>.md

    rag_api_min_niveau: str = "prediagnostic_qualitatif"  # score >= 40% requis pour basculer vers l'API (doc 07 §5)
    rag_api_long_message_chars: int = 200
    rag_api_keywords: tuple[str, ...] = (
        "audit", "combien", "coût", "cout", "prix", "rentab", "chiffr", "économie", "economie",
    )

    # --- Simulateur solaire (doc 09 §1) — ordres de grandeur France 2026, À CALIBRER, jamais donnés comme certains ---
    # Prix du kWh évité par l'autoconsommation. TRV option Base au 1er août 2026 :
    # 0,2001 €/kWh TTC jusqu'à 6 kVA, 0,1985 € à partir de 9 kVA. Valeur prudente retenue : 0,20.
    solar_prix_achat_eur_kwh: float = 0.20
    # Rachat du surplus résidentiel : 1,1 c€/kWh depuis l'arrêté du 1er juin 2026 (réforme S21),
    # qui a aussi supprimé la prime à l'autoconsommation. C'était 0,13 € avant la réforme —
    # une valeur périmée surestimait la rentabilité d'un facteur 12 sur cette ligne.
    # La rentabilité du solaire repose désormais sur l'autoconsommation, pas sur la revente.
    solar_prix_revente_eur_kwh: float = 0.011
    solar_conso_defaut_kwh_an: int = 4500        # conso annuelle par défaut (mode public sans fiche)
    solar_autoconso_sans_pilotage: float = 0.30  # part de la production consommée sur place, sans pilotage
    solar_autoconso_avec_pilotage: float = 0.45  # avec pilotage ballon + usages décalés
    solar_gain_autoconso_batterie: float = 0.25  # points d'autoconso gagnés avec batterie
    # Coût d'installation clé en main (€/kWc, hors batterie). Une grille par palier et non un
    # taux unique : le prix au kWc BAISSE fortement avec la puissance (coûts fixes d'étude, de
    # pose et de raccordement amortis sur plus de panneaux). Un taux unique fausserait justement
    # la comparaison 3/6/9 kWc que produit le simulateur.
    # Calée sur les devis réels AD Solar (2026) : 3 kWc ~2 170, 6 kWc ~1 700, 9 kWc ~1 600,
    # 13 kWc ~1 270 €/kWc. Valeurs interpolées entre les paliers (cf. solar_engine).
    # SOURCE ASSUMÉE, À RECALIBRER : ces prix viennent d'un seul installateur. Hélios se veut
    # neutre — on garde la provenance visible plutôt que de l'effacer, et on l'élargit à des
    # sources publiques dès qu'on en dispose.
    solar_cout_paliers_kwc: tuple[tuple[int, int], ...] = (
        (3, 2100), (6, 1750), (9, 1600), (12, 1400),
    )
    solar_cout_par_kwc_eur: int = 1750           # repli si la grille est indisponible
    solar_cout_batterie_par_kwh_eur: int = 700   # coût batterie LFP posée (€/kWh utile)
    solar_incertitude: float = 0.12              # demi-largeur des fourchettes affichées (±12 %)

    # --- Pré-audit (doc 07 §6) ---
    audit_version: str = "v1"                    # version du moteur, stockée dans audits.version_helios
    audit_min_completeness: float = 70.0         # complétude minimale pour générer un pré-audit chiffré (doc 02)
    audit_incertitude: float = 0.15              # demi-largeur des fourchettes (±15 %) — pré-audit = ordres de grandeur

    # --- Espace énergie / SOBRY (doc 09 §2) ---
    sobry_spot_api_url: str = ""                 # API publique SOBRY (prix spot quart-horaire) — vide = courbe de démo
    sobry_seuil_gain_pct: float = 5.0            # règle des 5 % : sous ce gain, Helios déconseille de changer (FAQ)
    energie_comparateur_public: str = "https://comparateur.energie-info.fr"  # à toujours mentionner (garde-fou doc 09 §2)

    # --- Courtage énergie (partenaire courtier, à nommer plus tard) ---
    courtage_partner_link: str = ""              # lien apporteur du courtier (vide = pas de lien proposé)
    courtage_gain_estime_pct: float = 8.0        # gain moyen estimé d'un changement d'offre via courtage (à calibrer)
    courtage_gain_estime_pct_pro: float = 12.0   # potentiel plus élevé en pro (volumes, contrats négociables)

    # --- Simulateur "Autoconso" (doc futur) : PV + batterie + tarifs dynamiques, à conso réelle ---
    # Enedis DataConnect (OAuth2) — identifiants d'un vrai partenaire homologué, obtenus après
    # inscription au Data Hub Enedis (SIRET, dossier RGPD/DPIA, callback HTTPS public). Vides en
    # dev : le moteur utilise une courbe de charge SIMULÉE tant que ces clés ne sont pas fournies.
    enedis_client_id: str = ""
    enedis_client_secret: str = ""
    enedis_redirect_uri: str = ""

    # Batterie physique — mêmes ordres de grandeur que solar_engine.STORAGE_TECHS
    autoconso_battery_efficiency: float = 0.90        # rendement aller-retour (pertes onduleur/charge)

    # MyLight — batterie virtuelle "MyBattery" (offre publique mylight150, tarifs 2026 relevés sur
    # le web le 22/07/2026 : papernest.com et adsolar.fr, concordants — À CONFIRMER auprès de MyLight
    # avant toute décision, ces montants peuvent évoluer). Nécessite de souscrire l'électricité chez
    # mylight150 (fournisseur alternatif) — contrainte réelle à signaler à l'utilisateur.
    # NEUTRALITÉ : adsolar.fr est l'une des deux sources concordantes relevées, pas la seule.
    # On garde la provenance affichée ; à recouper avec la grille officielle MyLight.
    mylight_activation_eur: float = 179.0
    mylight_abonnement_eur_par_kwc_mois: float = 1.20   # TTC
    mylight_restitution_eur_kwh: float = 0.083          # TURPE + accise (~4,93+3,37 cts HT)

    # SOBRY SoFlex / SoCap — grille de TEST fournie par l'utilisateur (structure réelle des offres,
    # valeurs à confirmer/mettre à jour auprès de SOBRY avant toute décision commerciale) :
    # SoFlex = tarif dynamique libre (marché), SoCap = même principe mais plafonné.
    sobry_soflex_prix_min_eur_kwh: float = -0.13   # tarifs négatifs possibles (surproduction réseau)
    sobry_soflex_prix_max_eur_kwh: float = 0.38
    sobry_soflex_heures_negatives_an: int = 1000   # ~1000 h/an à prix négatif ou nul
    sobry_socap_prix_min_eur_kwh: float = 0.00     # plafonné à 0 (jamais négatif), creux au midi solaire
    sobry_socap_prix_max_eur_kwh: float = 0.25     # plafonné la nuit

    # =====================================================================
    # Simulateur "maison + equipements" (etape 1) — TOUTES les hypotheses
    # sont ici et remontent a l'ecran via /api/simulateur/calcul ("hypotheses").
    # Chacune porte son statut : verifie / a recalibrer / a confirmer.
    # =====================================================================

    # --- Appels PVGIS ---
    # Une seule serie horaire par (lieu, inclinaison, orientation, pertes), pour 1 kWc :
    # toute puissance s'en deduit par multiplication. Les coordonnees sont ramenees sur une
    # grille : l'ensoleillement ne change pas sur 5 km, et un arrondi plus fin multiplierait
    # les appels sortants sur un point d'entree PUBLIC (PVGIS bloque les IP abusives).
    simu_pvgis_pas_grille_deg: float = 0.05
    simu_pvgis_cache_max: int = 128            # series gardees en memoire (~9 Mo)

    # --- Materiel ---
    simu_panneau_wc: int = 500                      # panneau de reference (a recalibrer)
    simu_panneau_surface_m2: float = 2.1            # pour "Remplir le toit" (a recalibrer)
    simu_panneaux_max: int = 40                     # borne haute du simulateur
    simu_carport_pente_deg: int = 5                 # carport : faible inclinaison, plein sud
    simu_carport_cout_par_panneau_eur: int = 250    # structure seule, hors panneau (a calibrer)
    simu_carport_tva_pct: float = 20.0              # carport a 20 % par defaut (A CONFIRMER)

    # --- Prix de l'electricite (TRV option Base au 1er aout 2026, verifie) ---
    # Le prix du kWh depend de la puissance souscrite : 0,2001 jusqu'a 6 kVA, 0,1985 des 9 kVA.
    simu_prix_kwh_par_kva: tuple[tuple[int, float], ...] = ((6, 0.2001), (9, 0.1985), (36, 0.1985))
    # Abonnement mensuel TTC par puissance souscrite (ordres de grandeur, A RECALIBRER).
    # Il n'entre pas dans les economies (il ne change pas avec le solaire) mais il est
    # AFFICHE dans la facture : sans lui, le chiffre ne correspond pas a la vraie facture.
    simu_abonnement_eur_mois_par_kva: tuple[tuple[int, float], ...] = (
        (3, 9.7), (6, 12.9), (9, 16.3), (12, 19.7), (15, 22.8), (18, 26.0), (24, 33.8), (30, 40.7), (36, 47.6),
    )

    # --- Raccordement ---
    simu_injection_max_kva_mono: float = 6.0        # plafond d'injection en monophase (verifie)

    # --- Fiscalite ---
    # TVA 5,5 % si <= 9 kWc, logement, SANS batterie physique, modules bas carbone,
    # gestion d'energie integree et installateur RGE ; sinon 20 % sur tout le projet.
    # La batterie virtuelle ne change pas la TVA. (verifie)
    simu_tva_seuil_kwc: float = 9.0
    simu_tva_reduite_pct: float = 5.5
    simu_tva_pleine_pct: float = 20.0

    # --- Economie sur 25 ans ---
    simu_duree_etude_ans: int = 25
    simu_hausse_prix_kwh_pct_an: float = 2.0        # defaut prudent ; selecteur 2/4/6 a l'ecran
    simu_hausse_prix_kwh_choix_pct: tuple[float, ...] = (2.0, 4.0, 6.0)
    simu_vieillissement_panneau_pct_an: float = 0.4  # A CALIBRER
    simu_revente_contrat_ans: int = 20              # contrat d'achat du surplus (verifie)
    simu_revente_indexation_pct_an: float = 2.0     # indexation du tarif de rachat (verifie)

    # --- Batterie physique (par packs) ---
    simu_batterie_pack_kwh: float = 5.0             # capacite utile d'un pack (a calibrer)
    simu_batterie_pack_kw: float = 2.5              # puissance de charge/decharge d'un pack
    simu_batterie_packs_max: int = 6
    simu_batterie_cout_par_kwh_eur: int = 700       # pose comprise (a calibrer)
    simu_batterie_perte_capacite_pct_an: float = 2.0
    simu_batterie_duree_vie_ans: int = 15           # au-dela : remplacement compte dans les 25 ans

    # --- Recherche de la meilleure taille ---
    # Un panneau de plus n'est retenu que si son gain marginal depasse ce rendement annuel.
    simu_seuil_rendement_marginal_pct: float = 5.0  # A CONFIRMER

    # --- Objectifs coches automatiquement ---
    simu_objectif_autonomie_pct: float = 50.0
    simu_objectif_retour_ans: int = 12
    simu_objectif_usages_pilotes: int = 2

    # --- Couches de consommation (kWh/an, ordres de grandeur A CALIBRER) ---
    # Base = electromenager + eclairage + veilles, hors chauffage/ECS/usages speciaux.
    simu_conso_base_fixe_kwh_an: int = 900          # socle du logement
    simu_conso_base_par_occupant_kwh_an: int = 450  # par personne
    simu_conso_veille_pct: float = 12.0             # part de la base qui tourne en continu
    # Chauffage : kWh/an par m2 chauffe, par type d'equipement.
    simu_conso_chauffage_kwh_m2_an: tuple[tuple[str, float], ...] = (
        ("elec_direct", 75.0), ("PAC_air_eau", 28.0), ("PAC_air_air", 30.0),
        ("gaz", 0.0), ("fioul", 0.0), ("bois", 0.0), ("reseau", 0.0), ("autre", 0.0),
    )
    # Eau chaude : kWh/an par occupant.
    simu_conso_ecs_kwh_occupant_an: tuple[tuple[str, float], ...] = (
        ("ballon_elec", 800.0), ("thermodynamique", 280.0),
        ("gaz", 0.0), ("solaire", 150.0), ("instantane", 700.0),
    )
    simu_conso_clim_kwh_piece_an: float = 250.0     # par piece climatisee, juin a septembre
    simu_conso_piscine_kwh_m3_an: float = 22.0      # filtration, mai a septembre, par m3 de bassin
    simu_conso_piscine_pompe_kw_defaut: float = 0.75
    simu_conso_ve_kwh_100km: float = 17.0           # consommation d'un vehicule electrique
    simu_conso_defaut_kwh_an: int = 4500            # repli si rien n'est connu

    # --- Batterie virtuelle : offres du marche (moteur generique, cf. batterie_virtuelle.py) ---
    # MySmartBattery : seuls les deux paliers extremes sont sources (12,99 EUR/mois a 20 kWh,
    # 214,99 EUR/mois a 10 000 kWh, activation 279 EUR). LA GRILLE INTERMEDIAIRE RESTE A RELEVER
    # ET A DATER aupres de MyLight — le simulateur signale qu'elle est incomplete plutot que
    # d'interpoler des paliers qui n'existent pas.
    simu_msb_activation_eur: float = 279.0
    simu_msb_paliers: tuple[tuple[int, float], ...] = ((20, 12.99), (10000, 214.99))
    simu_msb_grille_complete: bool = False

    # extra="ignore" : ce .env est partage avec docker compose (POSTGRES_*) et le pre-rendu SEO
    # (HELIOS_SITE_URL). Ces cles ne sont pas des reglages de l'API ; sans cette tolerance,
    # pydantic refuse de demarrer des qu'il rencontre une cle qu'il ne declare pas.
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")


settings = Settings()
