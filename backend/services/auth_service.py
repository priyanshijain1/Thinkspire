"""JWT Authentication service."""

import os
import re
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

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

_user_cache: dict[str, dict] = {}

# In-memory fallback for blacklist (when Redis unavailable)
_token_blacklist: set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain a number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain a special character (!@#$%^&*...)"
    return True, "Password is strong"


def get_password_strength(password: str) -> str:
    """Return password strength level."""
    if len(password) < 4:
        return "weak"
    score = 0
    if len(password) >= 8: score += 1
    if re.search(r"[A-Z]", password): score += 1
    if re.search(r"[a-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    
    if score <= 2:
        return "weak"
    elif score <= 3:
        return "medium"
    return "strong"


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return jwt.encode(
        {"username": username, "exp": expire, "type": "access"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_refresh_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    return jwt.encode(
        {"username": username, "exp": expire, "type": "refresh"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


async def _get_redis_client():
    """Get Redis client, returns None if unavailable."""
    try:
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            client = redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            return client
    except Exception:
        pass
    return None


async def invalidate_token(token: str) -> None:
    """Add token to blacklist (logout). Uses Redis with memory fallback."""
    redis_client = await _get_redis_client()
    
    if redis_client:
        try:
            # Calculate TTL from token expiration
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
                exp = payload.get("exp")
                if exp:
                    now = datetime.now(timezone.utc).timestamp()
                    ttl = max(0, int(exp - now))
                else:
                    ttl = ACCESS_TOKEN_EXPIRE_MINUTES * 60
            except JWTError:
                ttl = ACCESS_TOKEN_EXPIRE_MINUTES * 60
            
            await redis_client.setex(f"blacklist:{token}", ttl, "1")
            await redis_client.close()
            return
        except Exception:
            pass
    
    # Fallback to memory
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is in memory blacklist."""
    return token in _token_blacklist


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify token and check blacklist."""
    # Check memory blacklist first (for fallback tokens)
    if is_token_blacklisted(token):
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user from MongoDB."""
    global _user_cache
    
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
