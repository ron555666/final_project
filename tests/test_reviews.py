from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

client = TestClient(app)


def setup_admin_user():
    db = SessionLocal()

    try:
        permission = db.query(models.Permission).filter(
            models.Permission.permission_id == "create_store"
        ).first()

        if not permission:
            permission = models.Permission(
                permission_id="create_store",
                name="create_store"
            )
            db.add(permission)

        role = db.query(models.Role).filter(
            models.Role.role_id == "admin"
        ).first()

        if not role:
            role = models.Role(
                role_id="admin",
                name="admin"
            )
            db.add(role)

        if permission not in role.permissions:
            role.permissions.append(permission)

        user = db.query(models.User).filter(
            models.User.email == "admin@test.com"
        ).first()

        if not user:
            user = models.User(
                user_id="TEST_ADMIN",
                email="admin@test.com",
                password_hash=hash_password("AdminTest123!"),
                role_id="admin",
                status="active"
            )
            db.add(user)

        db.commit()

    finally:
        db.close()


def get_admin_token():
    setup_admin_user()

    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })

    return res.json()["access_token"]


def test_create_review():
    token = get_admin_token()

    client.post(
        "/api/admin/stores/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "store_id": "TEST_REVIEW_STORE",
            "name": "Test Review Store",
            "store_type": "regular",
            "status": "active",
            "latitude": 37.7851806,
            "longitude": -122.4068592,
            "address_street": "100 Market St",
            "address_city": "San Francisco",
            "address_state": "CA",
            "address_postal_code": "94103",
            "address_country": "USA",
            "phone": "415-555-1234",
            "services": ["pharmacy", "pickup"]
        }
    )

    res = client.post("/api/stores/TEST_REVIEW_STORE/reviews", json={
        "rating": 5,
        "comment": "Nice"
    })

    assert res.status_code == 200
    assert res.json()["rating"] == 5