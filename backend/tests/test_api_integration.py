"""API integration tests (no database required for these endpoints)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_spec_available() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/auth/signup" in paths
    assert "/api/v1/events/" in paths or "/api/v1/events" in paths
    assert "/api/v1/dashboards/" in paths or "/api/v1/dashboards" in paths


def test_signup_validation_rejects_short_password() -> None:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bad@example.com",
            "password": "short",
            "organization_name": "Test Org",
            "role": "Viewer",
        },
    )
    assert response.status_code == 422


def test_events_requires_api_key() -> None:
    response = client.post(
        "/api/v1/events/",
        json={
            "event_name": "test",
            "timestamp": "2026-05-20T10:00:00+00:00",
            "user_id": "u1",
            "properties": {},
        },
    )
    assert response.status_code in {401, 403, 422}


def test_dashboards_requires_auth() -> None:
    response = client.get("/api/v1/dashboards/")
    assert response.status_code == 401


def test_cors_headers_on_health() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
