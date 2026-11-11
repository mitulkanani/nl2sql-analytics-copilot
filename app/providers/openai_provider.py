import json

from openai import OpenAI

from app.models import GeneratedQuery


class OpenAIQueryProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        self.model = model

    def generate(self, question: str, schema: str) -> GeneratedQuery:
        system = (
            "You are a careful analytics SQL assistant. Generate one SQLite SELECT query "
            "using only the supplied schema. Never write, alter, delete, attach, inspect "
            "system tables, or use SQL comments. Avoid SELECT *. Use explicit columns. "
            "Use completed orders for realized revenue. The application independently "
            "validates every query and executes it against a read-only database."
        )
        user = f"APPROVED SCHEMA:\n{schema}\n\nBUSINESS QUESTION:\n{question}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "analytics_sql",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sql": {"type": "string"},
                            "explanation": {"type": "string"},
                            "chart_type": {"type": "string", "enum": ["table", "bar", "line", "pie"]},
                            "chart_x": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                            "chart_y": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        },
                        "required": ["sql", "explanation", "chart_type", "chart_x", "chart_y"],
                        "additionalProperties": False,
                    },
                },
            },
            temperature=0,
        )
        message = response.choices[0].message
        if message.refusal:
            raise ValueError("The model declined to generate this analytics query.")
        if not message.content:
            raise ValueError("The model returned an empty SQL response.")
        return GeneratedQuery.model_validate(json.loads(message.content))
