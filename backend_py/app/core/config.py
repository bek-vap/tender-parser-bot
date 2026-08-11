from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:Jafarbek123000566j@localhost:5400/tender"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    REDIS_URL: str = "redis://localhost:6379/0"

    TELEGRAM_BOT_TOKEN: str = "8847122346:AAGK0Rf6UyqZZnz6zxgRZuy0w1HQ2z3ub-c"
    TELEGRAM_ALERT_CHAT_ID: str = "-1003964212976"
    TELEGRAM_PROXY_URL: str | None = None  # Example: "http://proxy_user:password@proxy_host:port"
    TELEGRAM_BOT_POLLING: bool = True  # Enable/disable bot long polling in API process

    UZEX_VALIDATION: str = ""
    UZEX_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    )

    SCRAPE_EVERY_MINUTES: int = 15
    SCRAPE_HOUR: int = 9
    SCRAPE_MINUTE: int = 0

    # Winner checker (daily): all UZEX tenders without a Winner row
    WINNER_CHECK_HOUR: int = 9
    WINNER_CHECK_MINUTE: int = 0  # same as SCRAPE_HOUR by default (09:00 Tashkent)
    WINNER_DAYS_BACK: int = 365  # 0 = check all tenders in DB
    WINNER_BATCH_LIMIT: int = 0  # 0 = no limit per run
    WINNER_API_DELAY_SECONDS: float = 0.15  # pause between API calls

    # Google Sheets settings
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""  # JSON string of service account credentials
    GOOGLE_SHEETS_SPREADSHEET_NAME: str = "Tender Intelligence Platform"
    GOOGLE_SHEETS_SHARE_EMAIL: str = ""  # Email to share spreadsheet with
    GOOGLE_SHEETS_AUTO_EXPORT: bool = True  # Auto-export new tenders

    # Telegram API settings for channel monitoring
    TELEGRAM_API_ID: int = 0  # Get from my.telegram.org
    TELEGRAM_API_HASH: str = ""  # Get from my.telegram.org
    TELEGRAM_MONITOR_ENABLED: bool = False  # Enable/disable channel monitoring
    TELEGRAM_MONITOR_CHANNELS: str = ""  # JSON string of channels to monitor

    # CRM settings
    CRM_WEBHOOK_URL: str = ""  # URL for CRM webhook integration

    CRON_SECRET: str = "mycronsecret"  # secret token for cron jobs

    # Telegram Webhook settings (for Render deployment)
    # Set WEBHOOK_URL to your Render service URL, e.g. "https://myapp.onrender.com"
    # When set, the bot uses webhooks instead of long-polling (eliminates TelegramConflictError)
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = "telegram-webhook-secret-token"  # secret to verify Telegram requests


settings = Settings()
