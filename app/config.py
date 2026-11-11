import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Natural Language to SQL Analytics Copilot")
    environment: str = os.getenv("ENVIRONMENT", "development")
    ai_provider: str = os.getenv("AI_PROVIDER", "mock").lower()
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "./data/analytics.db"))
    max_rows: int = int(os.getenv("MAX_ROWS", "100"))
    query_timeout_seconds: float = float(os.getenv("QUERY_TIMEOUT_SECONDS", "3"))


settings = Settings()
