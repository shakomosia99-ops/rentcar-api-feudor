from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Role, User
from app.schemas.user import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(Role.admin)


def _get_other_user(user_id: int, admin: User, db: Session) -> User:
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own account")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    data: RoleUpdate,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    user = _get_other_user(user_id, admin, db)
    user.role = data.role
    db.commit()
    return user


@router.patch("/users/{user_id}/block", response_model=UserOut)
def set_blocked(
    user_id: int,
    blocked: bool = True,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    user = _get_other_user(user_id, admin, db)
    user.is_active = not blocked
    db.commit()
    return user