from app.config import settings
from app.seed import initialize_database


if __name__ == "__main__":
    initialize_database(settings.database_path)
    print(f"Initialized synthetic analytics database at {settings.database_path}")
