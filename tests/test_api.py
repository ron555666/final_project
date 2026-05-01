from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.routes.stores.geocode_location")
def test_search_with_mock(mock_geo):
    mock_geo.return_value = {
        "latitude": 37.77,
        "longitude": -122.41
    }

    response = client.post("/api/stores/search", json={
        "address": "San Francisco"
    })

    assert response.status_code == 200

    data = response.json()

    assert "metadata" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["metadata"]["latitude"] == 37.77
    assert data["metadata"]["longitude"] == -122.41
    