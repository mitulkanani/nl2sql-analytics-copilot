import argparse
import json

from app.config import settings
from app.history import QueryHistory
from app.seed import initialize_database
from app.service import AnalyticsService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask an analytics question in plain English.")
    parser.add_argument("question", nargs="+", help="Business question")
    args = parser.parse_args()
    initialize_database(settings.database_path)
    history = QueryHistory(settings.database_path.with_name("query_history.db"))
    history.initialize()
    result = AnalyticsService(settings, history).query(" ".join(args.question))
    print(json.dumps(result.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    main()
