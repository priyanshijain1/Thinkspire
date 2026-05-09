"""JWT Authentication service."""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import argon2
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Demo users - in production, load from database
USERS_DB = {
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
    """Verify password against hash."""
    return argon2.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password."""
    user = USERS_DB.get(username)
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return {"username": user["username"], "role": user["role"]}


def get_user_from_token(token: str) -> Optional[dict]:
    """Extract user info from token."""
    payload = verify_token(token)
    if payload:
        return {"username": payload.get("username"), "role": payload.get("role")}
    return None