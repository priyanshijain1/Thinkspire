"""Test fixtures and configuration."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch("backend.sessions.redis_session.get_client", new_callable=AsyncMock) as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_session():
    """Sample session data."""
    return {
        "hint_level": 0,
        "last_user_message": None,
        "last_ai_response": "",
        "repeat_count": 0,
    }