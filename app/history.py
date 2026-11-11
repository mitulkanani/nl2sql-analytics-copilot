import json
import sqlite3
from pathlib import Path
from typing import Any


class QueryHistory:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS query_history (
                    query_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    sql TEXT NOT NULL,
                    rows_returned INTEGER NOT NULL,
                    execution_ms REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )"""
            )
            connection.commit()

    def add(self, item: dict[str, Any]) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """INSERT INTO query_history
                (query_id, question, sql, rows_returned, execution_ms, created_at, provider, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item["query_id"], item["question"], item["sql"], item["rows_returned"],
                    item["execution_ms"], item["created_at"], item["provider"],
                    json.dumps(item.get("rows", []), default=str),
                ),
            )
            connection.commit()

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT query_id, question, sql, rows_returned, execution_ms, created_at, provider "
                "FROM query_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
