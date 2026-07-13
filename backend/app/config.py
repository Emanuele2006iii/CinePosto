"""Settings centralizzate caricate da .env (pydantic-settings)."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default CORS per sviluppo locale (Expo dev server, Metro bundler, web build).
# In produzione vengono sovrascritti da CORS_ORIGINS nel .env.
_DEV_CORS_DEFAULTS = [
    "http://localhost:8081",     # Metro bundler
    "http://localhost:19006",    # Expo web
    "http://localhost:3000",     # test web occasionale
]


class Settings(BaseSettings):
    """Configurazione dell'applicazione, letta da variabili d'ambiente e file .env.

    Ogni campo ha un default dev-friendly: il backend parte anche senza .env.
    In produzione i valori vanno espliciti (vedi .env.example per il formato:
    CORS_ORIGINS deve essere un array JSON, non CSV — limite di pydantic-settings 2.6).
    """

    # pydantic-settings: legge automaticamente i valori dal file .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"

    # DB: default dev-friendly (SQLite locale). In prod si passa via .env.
    database_url: str = "sqlite:///./cineposto.db"

    # Path del JSON scraper. Relativo alla cartella backend/ di default;
    # viene risolto a path assoluto al load, cosi' non dipende dalla CWD.
    scraper_output_dir: Path = Path("../scraper/output")

    # CORS: se .env non specifica CORS_ORIGINS, usa i default dev.
    cors_origins: list[str] = Field(default_factory=lambda: list(_DEV_CORS_DEFAULTS))

    # ADMIN TOKEN: nessun default insicuro. Se .env non lo setta,
    # viene generato al boot un token random (stampato ai log una volta).
    admin_token: str = ""

    @field_validator("scraper_output_dir", mode="after")
    @classmethod
    def _resolve_scraper_dir(cls, v: Path) -> Path:
        """Risolve il path a assoluto al load: il seed non dipende dalla CWD di lancio."""
        return v.expanduser().resolve()

    @field_validator("admin_token", mode="after")
    @classmethod
    def _generate_admin_token_if_empty(cls, v: str) -> str:
        """Garantisce un token admin sempre presente e mai banale.

        Se .env non lo imposta, o contiene il placeholder di sviluppo, viene
        generato un token random stampato una volta ai log: gli endpoint admin
        restano protetti anche su un'installazione non configurata.
        """
        if not v or v == "change-me-before-deploy":
            import secrets
            generated = secrets.token_urlsafe(32)
            print(
                f"⚠️  ADMIN_TOKEN non configurato in .env — generato al volo:\n"
                f"    {generated}\n"
                f"    (imposta ADMIN_TOKEN=... in .env per averlo stabile)"
            )
            return generated
        return v


@lru_cache
def get_settings() -> Settings:
    """Singleton delle Settings: il .env viene letto una volta sola per processo."""
    return Settings()
