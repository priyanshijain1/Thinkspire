"""Rate limiting service using Redis."""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory stores: request counts, failures, and lockout expiry
_rate_limit_store: dict[str, list[datetime]] = {}
_failure_store: dict[str, list[datetime]] = {}
_lockout_store: dict[str, datetime] = {}

# Failure threshold before lockout
FAILURE_THRESHOLD = 3


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

    def _cleanup_old(self, timestamps: list[datetime]) -> list[datetime]:
        """Remove timestamps outside the time window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        return [ts for ts in timestamps if ts > cutoff]

    async def is_allowed(self, identifier: str) -> tuple[bool, str, int]:
        """
        Check if request is allowed.

        Returns:
            (is_allowed, message, retry_after_seconds)
        """
        # Check Redis first
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
                await client.ping()

                # Check lockout
                lockout_key = f"ratelimit:lockout:{identifier}"
                lockout_ttl = await client.ttl(lockout_key)
                if lockout_ttl > 0:
                    await client.close()
                    return False, f"Too many failed attempts. Try again in {lockout_ttl} seconds.", lockout_ttl

                # Check request count
                key = f"ratelimit:{identifier}"
                count = await client.get(key)

                if count and int(count) >= self.max_requests:
                    ttl = await client.ttl(key)
                    await client.close()
                    return False, f"Rate limit exceeded. Try again in {ttl} seconds.", ttl

                # Increment counter
                pipe = client.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                await pipe.execute()
                await client.close()

                remaining = max(0, self.max_requests - int(count or 0) - 1)
                return True, f"OK ({remaining} requests remaining)", 0
        except Exception as e:
            logger.debug("Redis rate limit check failed, using memory: %s", e)

        # Memory fallback
        now = datetime.now()

        # Check lockout
        lockout_expiry = _lockout_store.get(identifier)
        if lockout_expiry and now < lockout_expiry:
            remaining = int((lockout_expiry - now).total_seconds())
            return False, f"Too many failed attempts. Try again in {remaining} seconds.", remaining
        elif lockout_expiry:
            # Lockout expired, clean up
            _lockout_store.pop(identifier, None)
            _failure_store.pop(identifier, None)

        # Rate limit check
        if identifier not in _rate_limit_store:
            _rate_limit_store[identifier] = []

        requests = self._cleanup_old(_rate_limit_store[identifier])

        if len(requests) >= self.max_requests:
            oldest = requests[0]
            ttl = max(1, int((oldest + timedelta(seconds=self.window_seconds) - now).total_seconds()))
            _rate_limit_store[identifier] = requests
            return False, f"Rate limit exceeded. Try again in {ttl} seconds.", ttl

        requests.append(now)
        _rate_limit_store[identifier] = requests

        remaining = self.max_requests - len(requests)
        return True, f"OK ({remaining} requests remaining)", 0

    async def record_failure(self, identifier: str) -> None:
        """Record a failed attempt. Triggers lockout after threshold."""
        # Memory: track failures
        if identifier not in _failure_store:
            _failure_store[identifier] = []

        _failure_store[identifier] = self._cleanup_old(_failure_store[identifier])
        _failure_store[identifier].append(datetime.now())

        if len(_failure_store[identifier]) >= FAILURE_THRESHOLD:
            _lockout_store[identifier] = datetime.now() + timedelta(seconds=self.lockout_seconds)
            logger.info("Identifier %s locked out for %d seconds", identifier, self.lockout_seconds)

        # Redis: track failures
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
                failures = await client.incr(f"ratelimit:failures:{identifier}")
                await client.expire(f"ratelimit:failures:{identifier}", self.window_seconds)

                if failures >= FAILURE_THRESHOLD:
                    await client.setex(f"ratelimit:lockout:{identifier}", self.lockout_seconds, "1")

                await client.close()
        except Exception as e:
            logger.debug("Redis record_failure failed: %s", e)

    async def reset(self, identifier: str) -> None:
        """Reset rate limit and failures for identifier (on success)."""
        _rate_limit_store.pop(identifier, None)
        _failure_store.pop(identifier, None)
        _lockout_store.pop(identifier, None)

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
                await client.close()
        except Exception as e:
            logger.debug("Redis rate limit reset failed: %s", e)


# Rate limiters for different endpoints
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=60, lockout_seconds=300)
signup_rate_limiter = RateLimiter(max_requests=3, window_seconds=300, lockout_seconds=600)
chat_rate_limiter = RateLimiter(max_requests=60, window_seconds=60)

# Backward-compatible alias
auth_rate_limiter = login_rate_limiter
