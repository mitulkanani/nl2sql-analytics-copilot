from fastapi import APIRouter, HTTPException, Query, Request

from app.catalog import public_schema
from app.models import HealthResponse, QueryHistoryItem, QueryRequest, QueryResult
from app.safety import SQLSafetyError
from app.executor import QueryExecutionError

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    service = request.app.state.analytics
    return HealthResponse(status="ok", provider=service.provider.name, database="ready")


@router.get("/schema")
def get_schema() -> dict[str, object]:
    return {"tables": public_schema(), "read_only": True}


@router.post("/query", response_model=QueryResult)
def run_query(payload: QueryRequest, request: Request) -> QueryResult:
    try:
        return request.app.state.analytics.query(payload.question)
    except SQLSafetyError as exc:
        raise HTTPException(status_code=422, detail=f"Query blocked by safety policy: {exc}") from exc
    except QueryExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        # Do not leak provider credentials or internal stack details to clients.
        raise HTTPException(status_code=502, detail="Query generation failed. Check provider configuration and server logs.") from exc


@router.get("/history", response_model=list[QueryHistoryItem])
def get_history(request: Request, limit: int = Query(default=20, ge=1, le=100)):
    return request.app.state.analytics.history.list(limit=limit)
