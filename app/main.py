from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.history import QueryHistory
from app.seed import initialize_database
from app.service import AnalyticsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database(settings.database_path)
    history = QueryHistory(settings.database_path.with_name("query_history.db"))
    history.initialize()
    app.state.analytics = AnalyticsService(settings, history)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "A safety-first natural-language analytics copilot. Generated SQL is validated "
        "against an approved schema and executed using read-only database protections."
    ),
    lifespan=lifespan,
)
app.include_router(router)

FRONTEND_DIR = Path(__file__).resolve().parent / "static"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", include_in_schema=False)
def root_health():
    return {"status": "ok", "docs": "/docs", "api": "/api/health"}
