"""MongoDB User database service."""

import logging
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
logger = logging.getLogger(__name__)


async def _connect():
    global _client, _db, _users_collection
    if _client is None:
        try:
            _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            _db = _client[DB_NAME]
            _users_collection = _db["users"]
            await _client.admin.command("ping")
            # Create index for username (fast lookups)
            await _users_collection.create_index("username", unique=True)
        except Exception:
            logger.exception("MongoDB connection failed")
            _client = None
            _db = None
            _users_collection = None


async def get_users_collection():
    global _users_collection
    if _users_collection is None:
        await _connect()
    return _users_collection


async def create_user(username: str, password_hash: str) -> dict:
    """Create a new user."""
    coll = await get_users_collection()
    if coll is None:
        raise Exception("Database unavailable")
    
    doc = {
        "username": username,
        "password_hash": password_hash,
    }
    try:
        await coll.insert_one(doc)
        return {"username": username}
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise ValueError(f"User '{username}' already exists")
        logger.exception("User creation failed for username '%s'", username)
        raise


async def get_user(username: str) -> Optional[dict]:
    """Get user by username."""
    coll = await get_users_collection()
    if coll is None:
        return None
    
    try:
        user = await coll.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception:
        return None
