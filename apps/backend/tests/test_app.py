from fastapi.testclient import TestClient

from bitnp_ideas.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_exposes_ideas() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/ideas" in response.text
    assert "/api/v1/ideas" not in response.text
