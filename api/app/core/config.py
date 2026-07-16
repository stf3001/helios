from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://helios:change-me@localhost:5432/helios"
    jwt_secret: str = "change-me"
    llm_api_provider: str = "anthropic"
    llm_api_key: str = ""            # emplacement réservé — clé à venir
    llm_api_budget_daily_eur: float = 5.0
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

    class Config:
        env_file = ".env"


settings = Settings()
