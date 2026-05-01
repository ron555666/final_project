from app.database import SessionLocal
from app import models
from app.utils.security import hash_password


db = SessionLocal()

users = [
    {
        "user_id": "U001",
        "email": "admin@test.com",
        "password": "AdminTest123!",
        "role": "admin"
    },
    {
        "user_id": "U002",
        "email": "marketer@test.com",
        "password": "MarketerTest123!",
        "role": "marketer"
    },
    {
        "user_id": "U003",
        "email": "viewer@test.com",
        "password": "ViewerTest123!",
        "role": "viewer"
    }
]

for user_data in users:
    existing_user = db.query(models.User).filter(
        models.User.email == user_data["email"]
    ).first()

    if existing_user:
        print(f"User already exists: {user_data['email']}")
        continue

    user = models.User(
        user_id=user_data["user_id"],
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        role=user_data["role"],
        status="active"
    )

    db.add(user)

db.commit()
db.close()

print("Seed users created successfully")