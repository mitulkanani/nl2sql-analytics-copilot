import sqlite3

import pytest

from app.safety import ValidatedSQL
from app.executor import ReadOnlyExecutor
from app.safety import SQLSafetyError


def test_executes_read_only_query(analytics_service) -> None:
    executor = analytics_service.executor
    columns, rows, truncated, elapsed = executor.execute(
        "SELECT status, COUNT(*) AS total FROM orders GROUP BY status ORDER BY total DESC"
    )
    assert columns == ["status", "total"]
    assert rows
    assert truncated is False
    assert elapsed >= 0


def test_result_limit_is_enforced(analytics_service) -> None:
    analytics_service.executor.max_rows = 3
    columns, rows, truncated, _ = analytics_service.executor.execute("SELECT id, name FROM customers")
    assert len(rows) == 3
    assert truncated is True


def test_database_is_not_modified_by_query(analytics_service) -> None:
    database = analytics_service.settings.database_path
    before = sqlite3.connect(database).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    analytics_service.executor.execute("SELECT COUNT(*) AS total FROM orders")
    after = sqlite3.connect(database).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert before == after


def test_authorizer_blocks_system_table_reads(analytics_service, monkeypatch) -> None:
    # Bypass the front-door validator to verify the database authorizer itself.
    monkeypatch.setattr(
        "app.executor.validate_sql",
        lambda _sql: ValidatedSQL(
            sql="SELECT name FROM sqlite_master",
            tables=("sqlite_master",),
            validator="test-bypass",
        ),
    )
    with pytest.raises(SQLSafetyError):
        analytics_service.executor.execute("SELECT name FROM sqlite_master")
