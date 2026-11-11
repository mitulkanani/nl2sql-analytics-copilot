import sqlite3
import time
from pathlib import Path
from typing import Any

from app.catalog import ALLOWED_TABLES
from app.safety import SQLSafetyError, validate_sql


class QueryExecutionError(RuntimeError):
    """Raised when a read-only analytics query cannot be executed."""


class ReadOnlyExecutor:
    def __init__(self, database_path: Path, max_rows: int = 100, timeout_seconds: float = 3.0):
        self.database_path = database_path
        self.max_rows = max(1, max_rows)
        self.timeout_seconds = max(0.1, timeout_seconds)

    def execute(self, sql: str) -> tuple[list[str], list[dict[str, Any]], bool, float]:
        validated = validate_sql(sql)
        if not self.database_path.exists():
            raise QueryExecutionError("Analytics database is not initialized.")

        uri = f"file:{self.database_path.resolve().as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
        connection.row_factory = sqlite3.Row
        start = time.perf_counter()
        deadline = start + self.timeout_seconds

        def authorize(action: int, arg1: str | None, arg2: str | None, db_name: str | None, trigger: str | None) -> int:
            allowed_actions = {
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_FUNCTION,
            }
            recursive_action = getattr(sqlite3, "SQLITE_RECURSIVE", -999)
            if action == recursive_action:
                return sqlite3.SQLITE_OK
            if action not in allowed_actions:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_READ and (arg1 or "").lower() not in ALLOWED_TABLES:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION:
                function_name = (arg2 or arg1 or "").lower()
                if function_name in {"load_extension", "readfile", "writefile", "fts3_tokenizer"}:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        def time_limit() -> int:
            return 1 if time.perf_counter() > deadline else 0

        try:
            # query_only is an additional guard; the authorizer below is the
            # primary statement/table policy and the URI is opened mode=ro.
            connection.execute("PRAGMA query_only = ON")
            connection.set_authorizer(authorize)
            connection.set_progress_handler(time_limit, 1000)
            limited_sql = f"SELECT * FROM ({validated.sql}) AS _copilot_result LIMIT {self.max_rows + 1}"
            cursor = connection.execute(limited_sql)
            rows_raw = cursor.fetchall()
            columns = [description[0] for description in cursor.description or []]
            truncated = len(rows_raw) > self.max_rows
            rows_raw = rows_raw[: self.max_rows]
            rows = [dict(row) for row in rows_raw]
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return columns, rows, truncated, elapsed_ms
        except sqlite3.DatabaseError as exc:
            message = str(exc)
            if "interrupted" in message.lower():
                raise QueryExecutionError(
                    f"Query exceeded the {self.timeout_seconds:.1f}s execution timeout."
                ) from exc
            if "not authorized" in message.lower() or "prohibited" in message.lower():
                raise SQLSafetyError("The database rejected an operation outside the read-only policy.") from exc
            raise QueryExecutionError(f"Query could not be executed: {message}") from exc
        finally:
            connection.close()
