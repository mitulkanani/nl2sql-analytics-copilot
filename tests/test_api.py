import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # Entering the context manager runs the app lifespan and initializes the DB.
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_schema_endpoint_lists_approved_tables(client: TestClient) -> None:
    response = client.get("/api/schema")
    assert response.status_code == 200
    names = {table["name"] for table in response.json()["tables"]}
    assert names == {"customers", "products", "orders", "order_items"}


def test_query_endpoint_returns_results(client: TestClient) -> None:
    response = client.post("/api/query", json={"question": "Show monthly revenue trend"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "line"
    assert payload["rows_returned"] > 0


def test_query_endpoint_validates_input(client: TestClient) -> None:
    response = client.post("/api/query", json={"question": "x", "unexpected": True})
    assert response.status_code == 422


def test_history_endpoint_returns_prior_queries(client: TestClient) -> None:
    client.post("/api/query", json={"question": "Show revenue by region"})
    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.json()


def test_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "DataPilot" in response.text


def test_dashboard_assets_are_served(client: TestClient) -> None:
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert "renderResult" in response.text
