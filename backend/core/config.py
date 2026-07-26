from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "SaaS Trading Bot"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_saas"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Encryption key for Binance API keys (Fernet — 32 url-safe base64 bytes)
    FERNET_KEY: str = "change-me-generate-with-Fernet.generate_key()"

    # CORS — comma-separated list, e.g. "http://localhost:3000,https://yourapp.vercel.app"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Normalize whatever the host injects into an asyncpg URL.

        Railway/Heroku Postgres plugins hand out `postgres://` or
        `postgresql://` URLs, but create_async_engine needs the
        `postgresql+asyncpg://` driver prefix. Also strip libpq-style
        `sslmode`/`ssl` query params that asyncpg does not understand.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        # asyncpg rejects libpq's sslmode/ssl query params — drop them.
        if "?" in url:
            base, _, query = url.partition("?")
            kept = [
                p for p in query.split("&")
                if p and p.split("=")[0].lower() not in ("sslmode", "ssl")
            ]
            url = base + ("?" + "&".join(kept) if kept else "")
        return url


settings = Settings()
