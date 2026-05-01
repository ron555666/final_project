from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

client = TestClient(app)


def setup_admin_user():
    db = SessionLocal()

    try:
        role = db.query(models.Role).filter(
            models.Role.role_id == "admin"
        ).first()

        if not role:
            role = models.Role(
                role_id="admin",
                name="admin"
            )
            db.add(role)

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


def test_login_and_access_protected():
    setup_admin_user()

    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })

    assert res.status_code == 200

    token = res.json()["access_token"]

    response = client.get(
        "/api/admin/stores/?skip=0&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_login_success():
    setup_admin_user()

    res = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminTest123!"
    })

    assert res.status_code == 200
    assert "access_token" in res.json()