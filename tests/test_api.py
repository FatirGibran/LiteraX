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

def test_api_matrix_export_endpoint():
    payload = {
        "matrix": {
            "topic": "IoT Security",
            "rows": [
                {
                    "paper_title": "IoT Security Survey",
                    "authors": "Smith et al.",
                    "year": 2024,
                    "method": "SVM",
                    "dataset": "CIC-IoT-2023",
                    "result": "High classification accuracy",
                    "limitation": "Bounded dataset",
                    "doi": "10.1016/j.iot.2024.01"
                }
            ]
        },
        "format": "markdown"
    }
    response = client.post("/api/v1/matrix/export", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "markdown"
    assert "| **IoT Security Survey** |" in data["content"]

def test_api_collections_lifecycle():
    user_id = "test_user_api"
    paper_payload = {
        "id": "paper_api_1",
        "title": "Adversarial Machine Learning",
        "doi": "10.1145/adv.ml.2024",
        "year": 2024,
        "source": "OpenAlex",
        "citation_count": 5
    }

    resp = client.post(f"/api/v1/collections/{user_id}/papers", json=paper_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "added"

    resp = client.get(f"/api/v1/collections/{user_id}")
    assert resp.status_code == 200
    papers = resp.json()
    assert len(papers) == 1
    assert papers[0]["title"] == "Adversarial Machine Learning"

    resp = client.get(f"/api/v1/collections/{user_id}/export?format=bibtex")
    assert resp.status_code == 200
    assert "@article{" in resp.json()["content"]

    resp = client.delete(f"/api/v1/collections/{user_id}/papers/paper_api_1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"

def test_api_benchmark_endpoint():
    response = client.post("/api/v1/benchmark/dedup", json={"base_count": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["total_input"] > 5
    assert data["expected_unique"] == 5
    assert data["precision"] > 0
    assert data["f1_score"] > 0


def test_api_openapi_metadata():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert "/api/v1/search" in paths
    search_op = paths["/api/v1/search"]["post"]
    assert "Search & Aggregation" in search_op["tags"]
    assert search_op["summary"] == "Search and aggregate literature"
    assert "/api/v1/correct" in paths
    assert "Fuzzy Search" in paths["/api/v1/correct"]["post"]["tags"]

