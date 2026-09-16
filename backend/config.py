from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuração central da aplicação, lida de variáveis de ambiente / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----- Ambiente -----
    ENVIRONMENT: str = "development"  # development | production

    # ----- CORS -----
    CORS_ORIGINS: str = "http://localhost:8501"

    # ----- Segurança -----
    SECRET_KEY: str = "troque-por-uma-chave-segura-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ----- Banco de dados -----
    DATABASE_URL: str = "sqlite+aiosqlite:///./contas_pagar.db"

    # ----- Seed inicial (apenas desenvolvimento) -----
    ADMIN_NAME : str = "Administrador"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_PASSWORD: str = "admin123"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()