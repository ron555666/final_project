from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_and_access_protected():
    # login
    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })

    token = res.json()["access_token"]

    # access protected endpoint
    res2 = client.post(
        "/api/stores/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "store_id": "INT001",
            "name": "Integration Test",
            "store_type": "flagship",
            "status": "active",
            "latitude": 37.77,
            "longitude": -122.41,
            "address_street": "123 Test",
            "address_city": "SF",
            "address_state": "CA",
            "address_postal_code": "94105",
            "address_country": "USA"
        }
    )

    assert res2.status_code in [200, 400]