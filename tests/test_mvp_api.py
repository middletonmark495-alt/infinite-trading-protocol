from fastapi.testclient import TestClient

from src.python.api.mvp import app

client = TestClient(app)


def test_health_is_read_only():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["execution_enabled"] is False


def test_root_advertises_docs_and_read_only_mode():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "read_only"
    assert body["execution_enabled"] is False
    assert body["docs"] == "/docs"


def test_risk_endpoint():
    response = client.post(
        "/risk/score",
        json={
            "concentration": 0.8,
            "volatility": 0.7,
            "liquidity_risk": 0.6,
            "stablecoin_share": 0.2,
        },
    )
    assert response.status_code == 200
    assert 0 <= response.json()["score"] <= 100


def test_execution_is_locked():
    response = client.get("/execution")
    assert response.status_code == 200
    assert response.json()["enabled"] is False
