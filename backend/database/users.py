"""MongoDB User database service."""

import os
from typing import Optional
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "thinkinspire")

_client: AsyncIOMotorClient | None = None
_db = None
_users_collection = None


async def _connect():
    global _client, _db, _users_collection
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[DB_NAME]
        _users_collection = _db["users"]
        try:
            await _users_collection.create_index("username", unique=True)
        except Exception:
            pass


async def get_users_collection():
    global _users_collection
    if _users_collection is None:
        await _connect()
    return _users_collection


async def create_user(username: str, password_hash: str, role: str = "student") -> dict:
    """Create a new user."""
    coll = await get_users_collection()
    doc = {
        "username": username,
        "password_hash": password_hash,
        "role": role,
    }
    try:
        await coll.insert_one(doc)
        return {"username": username, "role": role}
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise ValueError(f"User '{username}' already exists")
        raise


async def get_user(username: str) -> Optional[dict]:
    """Get user by username."""
    coll = await get_users_collection()
    try:
        user = await coll.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception:
        return None


async def get_all_users() -> list[dict]:
    """Get all users (without passwords)."""
    coll = await get_users_collection()
    try:
        users = await coll.find({}, {"password_hash": 0}).to_list(100)
        for u in users:
            u["_id"] = str(u["_id"])
        return users
    except Exception:
        return []


async def update_password(username: str, new_password_hash: str) -> bool:
    """Update user password."""
    coll = await get_users_collection()
    result = await coll.update_one(
        {"username": username},
        {"$set": {"password_hash": new_password_hash}}
    )
    return result.modified_count > 0


async def delete_user(username: str) -> bool:
    """Delete user."""
    coll = await get_users_collection()
    result = await coll.delete_one({"username": username})
    return result.deleted_count > 0


async def seed_demo_users():
    """Seed demo users if they don't exist."""
    from passlib.hash import argon2
    
    demo_users = [
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "student", "password": "student123", "role": "student"},
    ]
    
    for u in demo_users:
        existing = await get_user(u["username"])
        if not existing:
            await create_user(
                u["username"],
                argon2.hash(u["password"]),
                u["role"]
            )