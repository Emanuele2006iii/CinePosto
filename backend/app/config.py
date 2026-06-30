"""Settings centralizzate caricate da .env (pydantic-settings)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Dice a pydantic: leggi i valori dal file ".env"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # I campi qui sotto corrispondono 1:1 alle righe nel file .env
    database_url: str = "sqlite:///./cineposto.db"
    scraper_output_dir: Path = Path("../scraper/output")
    # Nel .env CORS_ORIGINS e' un JSON array: ["http://a","http://b"]
    cors_origins: list[str] = []
    env: str = "development"
    log_level: str = "INFO"
    admin_token: str = "change-me-before-deploy"


# lru_cache = chiama Settings() una sola volta, poi riusa il risultato.
# Cosi' non rileggi il .env a ogni richiesta HTTP.
@lru_cache
def get_settings() -> Settings:
    return Settings()
