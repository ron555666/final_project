from unittest.mock import patch
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.database import SessionLocal
from app import models

client = TestClient(app)


def get_or_create_service(db, name):
    service = db.query(models.Service).filter(
        models.Service.name == name
    ).first()

    if not service:
        service = models.Service(
            service_id=str(uuid.uuid4()),
            name=name
        )
        db.add(service)
        db.flush()

    return service


def setup_search_store(store_id="SEARCH_TEST_STORE"):
    db = SessionLocal()

    try:
        pharmacy = get_or_create_service(db, "pharmacy")
        pickup = get_or_create_service(db, "pickup")

        store = db.query(models.Store).filter(
            models.Store.store_id == store_id
        ).first()

        if not store:
            store = models.Store(
                store_id=store_id,
                name="Search Test Store",
                store_type="regular",
                status="active",
                latitude=37.7851806,
                longitude=-122.4068592,
                address_street="100 Market St",
                address_city="San Francisco",
                address_state="CA",
                address_postal_code="94103",
                address_country="USA",
                phone="415-555-1234",
                services="pharmacy|pickup",
                hours_mon="00:00-23:59",
                hours_tue="00:00-23:59",
                hours_wed="00:00-23:59",
                hours_thu="00:00-23:59",
                hours_fri="00:00-23:59",
                hours_sat="00:00-23:59",
                hours_sun="00:00-23:59"
            )
            db.add(store)

        store.status = "active"
        store.store_type = "regular"
        store.latitude = 37.7851806
        store.longitude = -122.4068592
        store.services = "pharmacy|pickup"
        store.service_items = [pharmacy, pickup]

        db.commit()

    finally:
        db.close()


@patch("app.routes.stores.geocode_location")
def test_search_by_address_with_mock(mock_geo):
    setup_search_store()

    mock_geo.return_value = {
        "latitude": 37.7851806,
        "longitude": -122.4068592
    }

    response = client.post("/api/stores/search", json={
        "address": "San Francisco"
    })

    assert response.status_code == 200

    data = response.json()

    assert "metadata" in data
    assert "results" in data
    assert isinstance(data["results"], list)


@patch("app.routes.stores.geocode_location")
def test_search_by_zip_with_mock(mock_geo):
    setup_search_store()

    mock_geo.return_value = {
        "latitude": 37.7851806,
        "longitude": -122.4068592
    }

    response = client.post("/api/stores/search", json={
        "postal_code": "94103",
        "radius_miles": 10
    })

    assert response.status_code == 200
    assert "results" in response.json()


def test_search_by_coordinates_and_filters():
    setup_search_store()

    response = client.post("/api/stores/search", json={
        "latitude": 37.7851806,
        "longitude": -122.4068592,
        "radius_miles": 10,
        "store_types": ["regular"],
        "services": ["pharmacy", "pickup"],
        "open_now": True,
        "min_rating": 0
    })

    assert response.status_code == 200

    data = response.json()

    assert "metadata" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_search_missing_location():
    response = client.post("/api/stores/search", json={
        "radius_miles": 10
    })

    assert response.status_code == 400
    assert "Provide either latitude/longitude" in response.json()["detail"]


def test_search_radius_too_large():
    response = client.post("/api/stores/search", json={
        "latitude": 37.7851806,
        "longitude": -122.4068592,
        "radius_miles": 101
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "radius_miles cannot exceed 100"