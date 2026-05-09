"""JWT Authentication service."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import argon2
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

_jwt_secret = os.getenv("JWT_SECRET")
if not _jwt_secret:
    _jwt_secret = secrets.token_urlsafe(32)
    
SECRET_KEY = _jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Cache for users to avoid repeated DB lookups
_user_cache: dict[str, dict] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user - single DB lookup with caching."""
    global _user_cache
    
    # Check cache first
    if username in _user_cache:
        user_doc = _user_cache[username]
    else:
        # DB lookup
        user_doc = None
        try:
            from database.users import get_user as db_get_user
            user_doc = await db_get_user(username)
            if user_doc:
                _user_cache[username] = user_doc
        except Exception:
            pass
    
    if not user_doc:
        return None
    
    if not verify_password(password, user_doc["password_hash"]):
        return None
    
    return {"username": user_doc["username"]}


def get_user_from_token(token: str) -> Optional[dict]:
    payload = verify_token(token)
    if payload:
        return {"username": payload.get("username")}
    return None