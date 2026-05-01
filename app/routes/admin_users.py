from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app import models, schemas
from app.utils.security import hash_password
from app.dependencies.permission import permission_required


router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin Users"]
)


@router.post("/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("manage_users"))
):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    role = db.query(models.Role).filter(
        models.Role.role_id == user.role_id
    ).first()

    if not role:
        raise HTTPException(status_code=400, detail="Invalid role_id")

    new_user = models.User(
        user_id=str(uuid.uuid4()),
        email=user.email,
        password_hash=hash_password(user.password),
        role_id=user.role_id,
        status=user.status
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=list[schemas.UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("manage_users"))
):
    return db.query(models.User).offset(skip).limit(limit).all()


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("manage_users"))
):
    user = db.query(models.User).filter(
        models.User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)

    if "role_id" in update_data:
        role = db.query(models.Role).filter(
            models.Role.role_id == update_data["role_id"]
        ).first()

        if not role:
            raise HTTPException(status_code=400, detail="Invalid role_id")

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("manage_users"))
):
    user = db.query(models.User).filter(
        models.User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = "inactive"
    db.commit()

    return {
        "message": "User deactivated successfully",
        "user_id": user.user_id,
        "status": user.status
    }