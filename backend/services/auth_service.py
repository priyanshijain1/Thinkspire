"""JWT Authentication service."""

import os
import secrets
from datetime import datetime, timedelta, timezone
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

# Short-lived access token: 15 minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 15
# Refresh token: 7 days
REFRESH_TOKEN_EXPIRE_DAYS = 7

# User cache
_user_cache: dict[str, dict] = {}

# Token blacklist for logout
_token_blacklist: set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)


def create_access_token(username: str) -> str:
    """Create short-lived access token (15 min)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return jwt.encode(
        {"username": username, "exp": expire, "type": "access"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_refresh_token(username: str) -> str:
    """Create long-lived refresh token (7 days)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    return jwt.encode(
        {"username": username, "exp": expire, "type": "refresh"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify token and check blacklist."""
    # Check blacklist
    if token in _token_blacklist:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        return payload
    except JWTError:
        return None


def invalidate_token(token: str) -> None:
    """Add token to blacklist (logout)."""
    _token_blacklist.add(token)


def is_token_invalidated(token: str) -> bool:
    return token in _token_blacklist


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user from MongoDB."""
    global _user_cache
    
    # Check cache first
    if username in _user_cache:
        user_doc = _user_cache[username]
    else:
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
    payload = verify_token(token, "access")
    if payload:
        return {"username": payload.get("username")}
    return None