"""Rate limiting service using Redis."""

from datetime import datetime, timedelta
from typing import Optional

# In-memory fallback rate limiter
_rate_limit_store: dict[str, list[datetime]] = {}


class RateLimiter:
    """Rate limiter with Redis backend and memory fallback."""

    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: int = 60,
        lockout_seconds: int = 300,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds

    def _cleanup_old_requests(self, requests: list[datetime]) -> list[datetime]:
        """Remove requests outside the time window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        return [req for req in requests if req > cutoff]

    def _is_locked_out(self, requests: list[datetime]) -> bool:
        """Check if identifier is locked out due to too many failures."""
        if not requests:
            return False
        # Check last request timestamp
        last_request = requests[-1]
        lockout_until = last_request + timedelta(seconds=self.lockout_seconds)
        return datetime.now() < lockout_until

    async def is_allowed(self, identifier: str) -> tuple[bool, str, int]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, message, retry_after_seconds)
        """
        global _rate_limit_store

        # Check Redis first
        redis_client = None
        try:
            import redis.asyncio as redis
            from pathlib import Path
            from dotenv import load_dotenv
            import os
            
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            redis_url = os.getenv("REDIS_URL")
            
            if redis_url:
                redis_client = redis.from_url(redis_url, decode_responses=True)
                await redis_client.ping()
                
                # Check lockout in Redis
                lockout_key = f"ratelimit:lockout:{identifier}"
                lockout_ttl = await redis_client.ttl(lockout_key)
                if lockout_ttl > 0:
                    return False, f"Too many failed attempts. Try again in {lockout_ttl} seconds.", lockout_ttl
                
                # Check request count in Redis
                key = f"ratelimit:{identifier}"
                count = await redis_client.get(key)
                
                if count and int(count) >= self.max_requests:
                    ttl = await redis_client.ttl(key)
                    return False, f"Rate limit exceeded. Try again in {ttl} seconds.", ttl
                
                # Increment counter
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                await pipe.execute()
                
                remaining = max(0, self.max_requests - int(count or 0) - 1)
                return True, f"OK ({remaining} requests remaining)", 0
        except Exception:
            pass

        # Fallback to memory
        now = datetime.now()

        if identifier not in _rate_limit_store:
            _rate_limit_store[identifier] = []

        requests = _rate_limit_store[identifier]

        # Check lockout
        if self._is_locked_out(requests):
            elapsed = (now - requests[-1]).total_seconds()
            remaining = max(0, self.lockout_seconds - elapsed)
            return False, f"Too many failed attempts. Try again in {int(remaining)} seconds.", int(remaining)

        # Cleanup old requests
        requests = self._cleanup_old_requests(requests)

        # Check limit
        if len(requests) >= self.max_requests:
            oldest = requests[0]
            ttl = int((oldest + timedelta(seconds=self.window_seconds) - now).total_seconds())
            return False, f"Rate limit exceeded. Try again in {max(1, ttl)} seconds.", max(1, ttl)

        # Add new request
        requests.append(now)
        _rate_limit_store[identifier] = requests

        remaining = self.max_requests - len(requests)
        return True, f"OK ({remaining} requests remaining)", 0

    async def record_failure(self, identifier: str) -> None:
        """Record a failed attempt (for login)."""
        global _rate_limit_store

        if identifier not in _rate_limit_store:
            _rate_limit_store[identifier] = []

        _rate_limit_store[identifier].append(datetime.now())

        # Try Redis
        try:
            import redis.asyncio as redis
            from pathlib import Path
            from dotenv import load_dotenv
            import os
            
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            redis_url = os.getenv("REDIS_URL")
            
            if redis_url:
                client = redis.from_url(redis_url, decode_responses=True)
                lockout_key = f"ratelimit:lockout:{identifier}"
                # Set lockout for 5 minutes after 3 failures
                failures = await client.incr(f"ratelimit:failures:{identifier}")
                await client.expire(f"ratelimit:failures:{identifier}", self.window_seconds)
                
                if failures >= 3:
                    await client.setex(lockout_key, self.lockout_seconds, "1")
        except Exception:
            pass

    async def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier (for successful login)."""
        global _rate_limit_store
        _rate_limit_store.pop(identifier, None)

        try:
            import redis.asyncio as redis
            from pathlib import Path
            from dotenv import load_dotenv
            import os
            
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            redis_url = os.getenv("REDIS_URL")
            
            if redis_url:
                client = redis.from_url(redis_url, decode_responses=True)
                await client.delete(f"ratelimit:{identifier}")
                await client.delete(f"ratelimit:failures:{identifier}")
                await client.delete(f"ratelimit:lockout:{identifier}")
        except Exception:
            pass


# Rate limiters for different endpoints
auth_rate_limiter = RateLimiter(max_requests=5, window_seconds=60, lockout_seconds=300)
chat_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)