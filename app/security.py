from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)

def _create_token(data: dict, lifetime:timedelta) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) +lifetime}
    return jwt.encode(payload, settings.secret_key, algorithm = settings. algorithm)

def create_access_token(user_id:int, role: str, session_jti:str )-> str:
    return _create_token(
        {"sub":str(user_id), "role":role, "sid":session_jti, "type":"access"},
        timedelta(minutes=settings.access_token_min),
    )

def create_refresh_token(user_id: int, session_jti: str) -> str:
    return _create_token(
        {"sub": str(user_id), "jti": session_jti, "type": "refresh"},
        timedelta(days=settings.refresh_token_days),
    )

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None
