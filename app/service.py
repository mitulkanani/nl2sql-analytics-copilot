from datetime import UTC, datetime
from uuid import uuid4

from app.catalog import public_schema, schema_for_prompt
from app.config import Settings
from app.executor import ReadOnlyExecutor
from app.history import QueryHistory
from app.models import GeneratedQuery, QueryResult
from app.providers.mock import MockQueryProvider
from app.safety import SQLSafetyError, validate_sql


class AnalyticsService:
    def __init__(self, settings: Settings, history: QueryHistory | None = None):
        self.settings = settings
        self.history = history or QueryHistory(settings.database_path.with_name("query_history.db"))
        self.executor = ReadOnlyExecutor(
            settings.database_path,
            max_rows=settings.max_rows,
            timeout_seconds=settings.query_timeout_seconds,
        )
        self.provider = self._create_provider()

    def _create_provider(self):
        if self.settings.ai_provider == "openai":
            if not self.settings.openai_api_key:
                raise RuntimeError("AI_PROVIDER=openai requires OPENAI_API_KEY.")
            from app.providers.openai_provider import OpenAIQueryProvider

            return OpenAIQueryProvider(self.settings.openai_api_key, self.settings.openai_model)
        if self.settings.ai_provider != "mock":
            raise RuntimeError("AI_PROVIDER must be either 'mock' or 'openai'.")
        return MockQueryProvider()

    def query(self, question: str) -> QueryResult:
        generated: GeneratedQuery = self.provider.generate(question, schema_for_prompt())
        validated = validate_sql(generated.sql)
        columns, rows, truncated, execution_ms = self.executor.execute(validated.sql)
        chart_x = generated.chart_x if generated.chart_x in columns else None
        chart_y = generated.chart_y if generated.chart_y in columns else None
        chart_type = generated.chart_type if chart_x and chart_y else "table"
        if chart_type == "table":
            chart_x = None
            chart_y = None

        created_at = datetime.now(UTC).isoformat()
        result = QueryResult(
            query_id=str(uuid4()),
            question=question,
            sql=validated.sql,
            explanation=generated.explanation,
            provider=self.provider.name,
            chart_type=chart_type,
            chart_x=chart_x,
            chart_y=chart_y,
            columns=columns,
            rows=rows,
            rows_returned=len(rows),
            truncated=truncated,
            execution_ms=execution_ms,
            created_at=created_at,
        )
        self.history.add(result.model_dump())
        return result

    @staticmethod
    def schema() -> list[dict[str, object]]:
        return public_schema()
