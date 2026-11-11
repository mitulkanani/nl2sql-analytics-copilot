from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=5, max_length=1000)


class GeneratedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(min_length=6, max_length=10000)
    explanation: str = Field(min_length=5, max_length=1000)
    chart_type: Literal["table", "bar", "line", "pie"]
    chart_x: str | None
    chart_y: str | None


class QueryResult(BaseModel):
    query_id: str
    question: str
    sql: str
    explanation: str
    provider: str
    chart_type: str
    chart_x: str | None
    chart_y: str | None
    columns: list[str]
    rows: list[dict[str, Any]]
    rows_returned: int
    truncated: bool
    execution_ms: float
    created_at: str


class QueryHistoryItem(BaseModel):
    query_id: str
    question: str
    sql: str
    rows_returned: int
    execution_ms: float
    created_at: str
    provider: str


class HealthResponse(BaseModel):
    status: str
    provider: str
    database: str
