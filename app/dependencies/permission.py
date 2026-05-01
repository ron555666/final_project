from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app import models


def permission_required(permission_name: str):

    def checker(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # get the role
        role = db.query(models.Role).filter(
            models.Role.role_id == current_user.role_id
        ).first()

        if not role:
            raise HTTPException(status_code=403, detail="Role not found")

        # check the permissions
        user_permissions = [p.name for p in role.permissions]

        if permission_name not in user_permissions:
            raise HTTPException(status_code=403, detail="Not enough permission")

        return current_user

    return checker

