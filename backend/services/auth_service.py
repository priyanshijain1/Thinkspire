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
    print(f"WARNING: JWT_SECRET not set. Generated temporary secret: {_jwt_secret[:10]}...")

SECRET_KEY = _jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Demo users fallback if MongoDB unavailable
_FALLBACK_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": argon2.hash("admin123"),
        "role": "admin",
    },
    "student": {
        "username": "student", 
        "password_hash": argon2.hash("student123"),
        "role": "student",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user - tries MongoDB first, falls back to hardcoded."""
    user_doc = None
    
    try:
        from database.users import get_user as db_get_user
        user_doc = await db_get_user(username)
    except Exception:
        pass
    
    if not user_doc:
        user_doc = _FALLBACK_USERS.get(username)
    
    if not user_doc:
        return None
    
    if not verify_password(password, user_doc["password_hash"]):
        return None
    
    return {"username": user_doc["username"], "role": user_doc["role"]}


def get_user_from_token(token: str) -> Optional[dict]:
    payload = verify_token(token)
    if payload:
        return {"username": payload.get("username"), "role": payload.get("role")}
    return None


async def get_all_users() -> list[str]:
    """Get all usernames."""
    try:
        from database.users import get_all_users as db_get_all
        users = await db_get_all()
        return [u["username"] for u in users]
    except Exception:
        return list(_FALLBACK_USERS.keys())


async def seed_users():
    """Seed demo users to MongoDB."""
    try:
        from database.users import seed_demo_users
        await seed_demo_users()
    except Exception:
        pass