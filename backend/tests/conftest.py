"""Test configuration."""
import os

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GROQ_API_KEY", "test_key")
