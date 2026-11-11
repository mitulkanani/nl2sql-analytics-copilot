from pathlib import Path

import pytest

from app.config import Settings
from app.history import QueryHistory
from app.seed import initialize_database
from app.service import AnalyticsService


@pytest.fixture
def analytics_service(tmp_path: Path) -> AnalyticsService:
    database = tmp_path / "analytics.db"
    initialize_database(database)
    history = QueryHistory(tmp_path / "history.db")
    history.initialize()
    settings = Settings(
        app_name="Test Copilot",
        environment="test",
        ai_provider="mock",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        database_path=database,
        max_rows=100,
        query_timeout_seconds=2.0,
    )
    return AnalyticsService(settings, history)
