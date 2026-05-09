"""Redis session storage with fallback to in-memory for testing."""

import os
import json
from typing import Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# In-memory fallback for when Redis is unavailable
_memory_store: dict[str, dict] = {}
_use_memory_fallback = False

_client = None


async def get_client():
    global _client, _use_memory_fallback
    
    if _use_memory_fallback:
        return None
    
    try:
        import redis.asyncio as redis
        if _client is None:
            _client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            await _client.ping()
        return _client
    except Exception:
        _use_memory_fallback = True
        return None


async def close_client():
    global _client, _use_memory_fallback
    if _client:
        await _client.close()
        _client = None
    _use_memory_fallback = False


async def load_session(session_id: str) -> Optional[dict[str, Any]]:
    client = await get_client()
    
    if client is None:
        # Use in-memory fallback
        return _memory_store.get(session_id)
    
    try:
        data = await client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    
    return _memory_store.get(session_id)


async def save_session(session_id: str, session_data: dict[str, Any], ttl_days: int = 7) -> None:
    client = await get_client()
    
    # Always save to memory as backup
    _memory_store[session_id] = session_data
    
    if client is None:
        return
    
    try:
        key = f"session:{session_id}"
        value = json.dumps(session_data)
        await client.set(key, value, ex=ttl_days * 24 * 60 * 60)
    except Exception:
        pass  # Already saved to memory


async def delete_session(session_id: str) -> None:
    client = await get_client()
    
    # Remove from memory
    _memory_store.pop(session_id, None)
    
    if client is None:
        return
    
    try:
        await client.delete(f"session:{session_id}")
    except Exception:
        pass


async def session_exists(session_id: str) -> bool:
    client = await get_client()
    
    if session_id in _memory_store:
        return True
    
    if client is None:
        return False
    
    try:
        return await client.exists(f"session:{session_id}") > 0
    except Exception:
        return False