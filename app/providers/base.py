from typing import Protocol

from app.models import GeneratedQuery


class QueryProvider(Protocol):
    name: str

    def generate(self, question: str, schema: str) -> GeneratedQuery: ...
