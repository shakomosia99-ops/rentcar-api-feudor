from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.models import Session as LoginSession
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)

def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: Session = Depends(get_db),
) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "invalid token"
    )
    if credentials is None:
        raise error
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise error

    login_session = db.scalar(
        select(LoginSession). where(LoginSession.jti == payload.get("sid"))
    )

    if login_session is None or login_session.revoked:
        raise error

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise error
    return user

def require_role(*allowed: Role):

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail = "წაი დაიკარგე!",
            )
        return user
    return checker

