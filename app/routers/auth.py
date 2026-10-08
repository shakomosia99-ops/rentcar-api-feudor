import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import bearer, get_current_user
from app.models import Session as LoginSession
from app.models import User
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, SessionOut, TokenOut
from app.schemas.user import UserOut
from app.security import  create_access_token, create_refresh_token,decode_token, hash_password,verify_password





router = APIRouter(prefix= "/auth", tags = ["auth"])

def _tokens_for(user:User, jti: str) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(user.id, user.role.value, jti),
        refresh_token=create_refresh_token(user.id,jti)
    )

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    taken = db.scalar(
        select(User).where(or_(User.phone == data.phone, User.email == data.email))
    )
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Phone or email already registered")

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.phone == data.phone))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong phone or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is blocked")
    
    jti = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    db.add(
        LoginSession(
            user_id=user.id,
            jti=jti,
            user_agent=(request.headers.get("user-agent") or "")[:255],
            expires_at=expires.replace(tzinfo=None),
        )
    )
    db.commit()
    return _tokens_for(user, jti)


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise error

    login_session = db.scalar(
        select(LoginSession).where(LoginSession.jti == payload.get("jti"))
    )
    if login_session is None or login_session.revoked:
        raise error
    user = db.get(User, login_session.user_id)
    if user is None or not user.is_active:
        raise error

    login_session.jti = str(uuid.uuid4())
    db.commit()
    return _tokens_for(user, login_session.jti)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    login_session = db.scalar(
        select(LoginSession).where(LoginSession.jti == payload["sid"])
    )
    login_session.revoked = True
    db.commit()


@router.get("/sessions", response_model=list[SessionOut])
def my_sessions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.scalars(
        select(LoginSession).where(
            LoginSession.user_id == user.id, LoginSession.revoked.is_(False)
        )
    ).all()