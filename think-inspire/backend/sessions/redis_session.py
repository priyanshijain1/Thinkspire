import os
import json
from typing import Any, Optional
from pathlib import Path

import redis.asyncio as redis
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: redis.Redis | None = None


async def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def close_client() -> None:
    global _client
    if _client:
        await _client.close()
        _client = None


async def load_session(session_id: str) -> Optional[dict[str, Any]]:
    client = await get_client()
    data = await client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return None


async def save_session(session_id: str, session_data: dict[str, Any], ttl_days: int = 7) -> None:
    client = await get_client()
    key = f"session:{session_id}"
    value = json.dumps(session_data)
    await client.set(key, value, ex=ttl_days * 24 * 60 * 60)


async def delete_session(session_id: str) -> None:
    client = await get_client()
    await client.delete(f"session:{session_id}")


async def session_exists(session_id: str) -> bool:
    client = await get_client()
    return await client.exists(f"session:{session_id}") > 0