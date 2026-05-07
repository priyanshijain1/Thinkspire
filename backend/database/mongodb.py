import os
import datetime as dt
from typing import Optional
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration from environment, with sensible defaults
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "thinkinspire")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "messages")

_client: AsyncIOMotorClient | None = None
_db = None
_collection = None


async def _connect():
    global _client, _db, _collection
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[DB_NAME]
        _collection = _db[COLLECTION_NAME]
        try:
            await _collection.create_index([("session_id", 1), ("timestamp", -1)])
        except Exception:
            pass


async def get_collection():
    global _collection
    if _collection is None:
        await _connect()
    return _collection


async def log_interaction(
    session_id: str,
    user_message: str,
    ai_response: str,
    hint_level: int,
    timestamp: Optional[dt.datetime] = None,
    intent: Optional[str] = None,
):
    coll = await get_collection()
    doc = {
        "session_id": session_id,
        "user_message": user_message,
        "ai_response": ai_response,
        "hint_level": int(hint_level),
        "timestamp": timestamp or dt.datetime.utcnow(),
        "intent": intent,
    }
    try:
        await coll.insert_one(doc)
    except Exception:
        # For now, swallow DB errors to avoid breaking API flow
        pass
