import pytest
from starlette.testclient import TestClient
from literax.api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_correct_endpoint():
    payload = {"query": "machin lerning untk deteksi phising"}
    response = client.post("/api/v1/correct", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["corrected_query"] == "machine learning untuk deteksi phishing"
    assert data["overall_confidence"] >= 0.90
    assert data["action"] == "AUTO_CORRECTED"

def test_api_citation_endpoint():
    response = client.get(
        "/api/v1/papers/test_1/citation",
        params={
            "title": "Machine Learning for Phishing",
            "year": 2025,
            "doi": "10.1016/j.cose.2024.103982",
            "style": "apa"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "https://doi.org/10.1016/j.cose.2024.103982" in data["citation"]
