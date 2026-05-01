from fastapi.testclient import TestClient
import uuid
from unittest.mock import patch

from app.main import app
from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

client = TestClient(app)


PERMISSIONS = [
    "view_store",
    "create_store",
    "update_store",
    "delete_store",
    "import_store",
    "manage_users"
]


def setup_roles_and_users():
    db = SessionLocal()

    try:
        permissions = []

        for permission_name in PERMISSIONS:
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

        admin_role = db.query(models.Role).filter(
            models.Role.role_id == "admin"
        ).first()

        if not admin_role:
            admin_role = models.Role(
                role_id="admin",
                name="admin"
            )
            db.add(admin_role)
            db.flush()

        for permission in permissions:
            if permission not in admin_role.permissions:
                admin_role.permissions.append(permission)

        viewer_role = db.query(models.Role).filter(
            models.Role.role_id == "viewer"
        ).first()

        if not viewer_role:
            viewer_role = models.Role(
                role_id="viewer",
                name="viewer"
            )
            db.add(viewer_role)

        admin_user = db.query(models.User).filter(
            models.User.email == "admin@test.com"
        ).first()

        if not admin_user:
            admin_user = models.User(
                user_id="TEST_ADMIN",
                email="admin@test.com",
                password_hash=hash_password("AdminTest123!"),
                role_id="admin",
                status="active"
            )
            db.add(admin_user)
        else:
            admin_user.password_hash = hash_password("AdminTest123!")
            admin_user.role_id = "admin"
            admin_user.status = "active"

        viewer_user = db.query(models.User).filter(
            models.User.email == "viewer@test.com"
        ).first()

        if not viewer_user:
            viewer_user = models.User(
                user_id="TEST_VIEWER",
                email="viewer@test.com",
                password_hash=hash_password("ViewerTest123!"),
                role_id="viewer",
                status="active"
            )
            db.add(viewer_user)
        else:
            viewer_user.password_hash = hash_password("ViewerTest123!")
            viewer_user.role_id = "viewer"
            viewer_user.status = "active"

        db.commit()

    finally:
        db.close()


def login(email, password):
    response = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })

    assert response.status_code == 200

    return response.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_refresh_logout_flow():
    setup_roles_and_users()

    login_data = login("admin@test.com", "AdminTest123!")

    assert "access_token" in login_data
    assert "refresh_token" in login_data

    refresh_response = client.post("/api/auth/refresh", json={
        "refresh_token": login_data["refresh_token"]
    })

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

    new_refresh_token = refresh_response.json()["refresh_token"]

    logout_response = client.post("/api/auth/logout", json={
        "refresh_token": new_refresh_token
    })

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"


def test_authentication_and_protected_endpoint_access():
    setup_roles_and_users()

    login_data = login("admin@test.com", "AdminTest123!")
    token = login_data["access_token"]

    response = client.get(
        "/api/admin/stores/?skip=0&limit=10",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_store_crud_operations():
    setup_roles_and_users()

    login_data = login("admin@test.com", "AdminTest123!")
    token = login_data["access_token"]

    store_id = f"CRUD_TEST_{uuid.uuid4()}"

    create_response = client.post(
        "/api/admin/stores/",
        headers=auth_headers(token),
        json={
            "store_id": store_id,
            "name": "CRUD Test Store",
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

    assert create_response.status_code == 200

    get_response = client.get(
        f"/api/admin/stores/{store_id}",
        headers=auth_headers(token)
    )
    assert get_response.status_code == 200

    update_response = client.patch(
        f"/api/admin/stores/{store_id}",
        headers=auth_headers(token),
        json={
            "name": "Updated CRUD Test Store",
            "services": ["pharmacy", "pickup"]
        }
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated CRUD Test Store"
    assert update_response.json()["services"] == "pharmacy|pickup"

    delete_response = client.delete(
        f"/api/admin/stores/{store_id}",
        headers=auth_headers(token)
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "inactive"


def test_viewer_cannot_create_store():
    setup_roles_and_users()

    login_data = login("viewer@test.com", "ViewerTest123!")
    token = login_data["access_token"]

    response = client.post(
        "/api/admin/stores/",
        headers=auth_headers(token),
        json={
            "store_id": f"VIEWER_TEST_{uuid.uuid4()}",
            "name": "Viewer Test Store",
            "store_type": "regular",
            "status": "active",
            "latitude": 37.7851806,
            "longitude": -122.4068592,
            "address_street": "100 Market St",
            "address_city": "San Francisco",
            "address_state": "CA",
            "address_postal_code": "94103",
            "address_country": "USA"
        }
    )

    assert response.status_code == 403


def test_csv_import_validation_bad_headers():
    setup_roles_and_users()

    login_data = login("admin@test.com", "AdminTest123!")
    token = login_data["access_token"]

    csv_content = "bad_header,name\n1,Test Store\n"

    response = client.post(
        "/api/admin/stores/import",
        headers=auth_headers(token),
        files={
            "file": ("bad.csv", csv_content, "text/csv")
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CSV headers do not match required format"


@patch("app.routes.stores.geocode_location")
def test_csv_import_with_geocoding(mock_geo):
    setup_roles_and_users()

    mock_geo.return_value = {
        "latitude": 37.7851806,
        "longitude": -122.4068592
    }

    login_data = login("admin@test.com", "AdminTest123!")
    token = login_data["access_token"]

    csv_content = (
        "store_id,name,store_type,status,latitude,longitude,"
        "address_street,address_city,address_state,address_postal_code,"
        "address_country,phone,services,hours_mon,hours_tue,hours_wed,"
        "hours_thu,hours_fri,hours_sat,hours_sun\n"
        "CSV_GEO_TEST,CSV Geo Test Store,regular,active,,,"
        "100 Market St,San Francisco,CA,94103,USA,415-555-1234,"
        "pharmacy|pickup,00:00-23:59,00:00-23:59,00:00-23:59,"
        "00:00-23:59,00:00-23:59,00:00-23:59,00:00-23:59\n"
    )

    response = client.post(
        "/api/admin/stores/import",
        headers=auth_headers(token),
        files={
            "file": ("stores.csv", csv_content, "text/csv")
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["failed"] == 0
    assert data["created"] + data["updated"] == 1

    store_response = client.get(
        "/api/admin/stores/CSV_GEO_TEST",
        headers=auth_headers(token)
    )

    assert store_response.status_code == 200
    assert store_response.json()["latitude"] == 37.7851806


def test_create_10_sample_stores_for_test_data():
    setup_roles_and_users()

    login_data = login("admin@test.com", "AdminTest123!")
    token = login_data["access_token"]

    for i in range(10):
        store_id = f"SAMPLE_STORE_{i}"

        response = client.post(
            "/api/admin/stores/",
            headers=auth_headers(token),
            json={
                "store_id": store_id,
                "name": f"Sample Store {i}",
                "store_type": "regular",
                "status": "active",
                "latitude": 37.7851806 + (i * 0.001),
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

        assert response.status_code in [200, 400]

    list_response = client.get(
        "/api/admin/stores/?skip=0&limit=20",
        headers=auth_headers(token)
    )

    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)