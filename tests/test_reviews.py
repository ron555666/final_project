from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

client = TestClient(app)


def setup_admin_user():
    db = SessionLocal()

    try:
        permissions_needed = ["create_store", "manage_users"]

        permissions = []

        for permission_name in permissions_needed:
            permission = db.query(models.Permission).filter(
                models.Permission.permission_id == permission_name
            ).first()

            if not permission:
                permission = models.Permission(
                    permission_id=permission_name,
                    name=permission_name
                )
                db.add(permission)
                db.flush()

            permissions.append(permission)

        role = db.query(models.Role).filter(
            models.Role.role_id == "admin"
        ).first()

        if not role:
            role = models.Role(
                role_id="admin",
                name="admin"
            )
            db.add(role)
            db.flush()

        for permission in permissions:
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
        else:
            user.password_hash = hash_password("AdminTest123!")
            user.role_id = "admin"
            user.status = "active"

        db.commit()

    finally:
        db.close()


def get_admin_token():
    setup_admin_user()

    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })

    assert res.status_code == 200

    return res.json()["access_token"]


def test_create_review_get_rating_and_flag_review():
    token = get_admin_token()

    store_id = f"REVIEW_TEST_{uuid.uuid4()}"

    create_store_response = client.post(
        "/api/admin/stores/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "store_id": store_id,
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

    assert create_store_response.status_code == 200

    create_review_response = client.post(f"/api/stores/{store_id}/reviews", json={
        "rating": 5,
        "comment": "Nice"
    })

    assert create_review_response.status_code == 200
    assert create_review_response.json()["rating"] == 5

    review_id = create_review_response.json()["review_id"]

    get_reviews_response = client.get(f"/api/stores/{store_id}/reviews")
    assert get_reviews_response.status_code == 200
    assert isinstance(get_reviews_response.json(), list)

    rating_response = client.get(f"/api/stores/{store_id}/rating")
    assert rating_response.status_code == 200
    assert rating_response.json()["average_rating"] == 5.0

    flag_response = client.patch(
        f"/api/stores/reviews/{review_id}/flag",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert flag_response.status_code == 200
    assert flag_response.json()["flagged"] is True


def test_invalid_review_rating_validation():
    response = client.post("/api/stores/NOT_EXIST/reviews", json={
        "rating": 10,
        "comment": "Invalid rating"
    })

    assert response.status_code == 422