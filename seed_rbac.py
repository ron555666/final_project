from app.database import SessionLocal
from app import models
from app.utils.security import hash_password


db = SessionLocal()

try:
    # 1. Permissions
    permission_names = [
        "create_store",
        "update_store",
        "delete_store",
        "view_store",
        "import_store",
        "manage_users",
        "manage_reviews"
    ]

    permissions = {}

    for name in permission_names:
        existing_permission = db.query(models.Permission).filter(
            models.Permission.name == name
        ).first()

        if existing_permission:
            permissions[name] = existing_permission
        else:
            permission = models.Permission(
                permission_id=name,
                name=name
            )
            db.add(permission)
            permissions[name] = permission

    db.flush()

    # 2. Roles
    role_data = [
        {"role_id": "admin", "name": "admin"},
        {"role_id": "marketer", "name": "marketer"},
        {"role_id": "viewer", "name": "viewer"},
    ]

    roles = {}

    for r in role_data:
        existing_role = db.query(models.Role).filter(
            models.Role.role_id == r["role_id"]
        ).first()

        if existing_role:
            roles[r["role_id"]] = existing_role
        else:
            role = models.Role(
                role_id=r["role_id"],
                name=r["name"]
            )
            db.add(role)
            roles[r["role_id"]] = role

    db.flush()

    # 3. Assign permissions to roles
    roles["admin"].permissions = list(permissions.values())

    roles["marketer"].permissions = [
        permissions["create_store"],
        permissions["update_store"],
        permissions["delete_store"],
        permissions["view_store"],
        permissions["import_store"],
    ]

    roles["viewer"].permissions = [
        permissions["view_store"],
    ]

    # 4. Users
    users_data = [
        {
            "user_id": "U001",
            "email": "admin@test.com",
            "password": "AdminTest123!",
            "role_id": "admin",
        },
        {
            "user_id": "U002",
            "email": "marketer@test.com",
            "password": "MarketerTest123!",
            "role_id": "marketer",
        },
        {
            "user_id": "U003",
            "email": "viewer@test.com",
            "password": "ViewerTest123!",
            "role_id": "viewer",
        },
    ]

    for u in users_data:
        existing_user = db.query(models.User).filter(
            models.User.email == u["email"]
        ).first()

        if existing_user:
            existing_user.role_id = u["role_id"]
            existing_user.status = "active"
        else:
            user = models.User(
                user_id=u["user_id"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role_id=u["role_id"],
                status="active"
            )
            db.add(user)

    db.commit()
    print("RBAC seed completed")

except Exception as e:
    db.rollback()
    print("RBAC seed failed:", e)

finally:
    db.close()
    
    