from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.database import get_db
from app import models, schemas
from app.utils.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    get_refresh_token_expiry,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["AUTH"]
)


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User inactive")

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role_id
    })

    refresh_token = create_refresh_token()

    db_token = models.RefreshToken(
        token_id=str(uuid.uuid4()),
        user_id=user.user_id,
        token_hash=hash_token(refresh_token),
        revoked=False,
        expires_at=get_refresh_token_expiry()
    )

    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    data: schemas.RefreshRequest,
    db: Session = Depends(get_db)
):
    hashed_token = hash_token(data.refresh_token)

    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == hashed_token,
        models.RefreshToken.revoked == False
    ).first()

    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(models.User).filter(
        models.User.user_id == token_record.user_id
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User inactive")

    token_record.revoked = True

    new_access_token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role_id
    })

    new_refresh_token = create_refresh_token()

    new_db_token = models.RefreshToken(
        token_id=str(uuid.uuid4()),
        user_id=user.user_id,
        token_hash=hash_token(new_refresh_token),
        revoked=False,
        expires_at=get_refresh_token_expiry()
    )

    db.add(new_db_token)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    data: schemas.LogoutRequest,
    db: Session = Depends(get_db)
):
    hashed_token = hash_token(data.refresh_token)

    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == hashed_token
    ).first()

    if token_record:
        token_record.revoked = True
        db.commit()

    return {"message": "Logged out successfully"}