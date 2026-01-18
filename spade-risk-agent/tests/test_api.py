from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_assess_endpoint_basic():
    payload = {
        "address": "123 Main St, Anytown, USA",
        "property_type": "home",
        "fenced": False,
        "gated": False,
        "operating_hours": "24/7",
        "notes": "recent theft in the area",
    }
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_dimensions" in data
    assert "overall_score" in data
    assert "confidence" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "api_sources_used" in data


