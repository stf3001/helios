from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://helios:change-me@localhost:5432/helios"
    jwt_secret: str = "change-me"
    admin_token: str = "change-me-admin"  # secret pour les endpoints admin (validation partenaires)
    llm_api_provider: str = "anthropic"
    llm_api_key: str = ""            # emplacement réservé — clé à venir
    llm_api_model: str = "claude-haiku-4-5-20251001"
    llm_api_budget_daily_eur: float = 5.0
    llm_api_budget_monthly_eur: float = 100.0
    llm_price_per_1k_tokens_eur: float = 0.005  # estimation grossière (blended in/out) — à calibrer
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    embed_model: str = "bge-m3"
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
    solar_prix_achat_eur_kwh: float = 0.25       # prix du kWh évité par l'autoconsommation (TRV ~2026)
    solar_prix_revente_eur_kwh: float = 0.13     # tarif de rachat du surplus (obligation d'achat < 9 kWc)
    solar_conso_defaut_kwh_an: int = 4500        # conso annuelle par défaut (mode public sans fiche)
    solar_autoconso_sans_pilotage: float = 0.30  # part de la production consommée sur place, sans pilotage
    solar_autoconso_avec_pilotage: float = 0.45  # avec pilotage ballon + usages décalés
    solar_gain_autoconso_batterie: float = 0.25  # points d'autoconso gagnés avec batterie
    solar_cout_par_kwc_eur: int = 2500           # coût installation clé en main (€/kWc, prime non déduite)
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

    # --- Simulateur "Revolt" (doc futur) : PV + batterie + tarifs dynamiques, à conso réelle ---
    # Enedis DataConnect (OAuth2) — identifiants d'un vrai partenaire homologué, obtenus après
    # inscription au Data Hub Enedis (SIRET, dossier RGPD/DPIA, callback HTTPS public). Vides en
    # dev : le moteur utilise une courbe de charge SIMULÉE tant que ces clés ne sont pas fournies.
    enedis_client_id: str = ""
    enedis_client_secret: str = ""
    enedis_redirect_uri: str = ""

    # Batterie physique — mêmes ordres de grandeur que solar_engine.STORAGE_TECHS
    revolt_battery_efficiency: float = 0.90        # rendement aller-retour (pertes onduleur/charge)

    # MyLight — batterie virtuelle "MyBattery" (offre publique mylight150, tarifs 2026 relevés sur
    # le web le 22/07/2026 : papernest.com et adsolar.fr, concordants — À CONFIRMER auprès de MyLight
    # avant toute décision, ces montants peuvent évoluer). Nécessite de souscrire l'électricité chez
    # mylight150 (fournisseur alternatif) — contrainte réelle à signaler à l'utilisateur.
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

    class Config:
        env_file = ".env"


settings = Settings()
