import pytest
from unittest.mock import AsyncMock, patch

import sys
import os

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.agent.agent import detect_intent, generate_response, main_agent


class TestDetectIntent:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("hello", "greeting"),
            ("Hi there", "greeting"),
            ("hey", "greeting"),
            ("greetings", "greeting"),
            ("what's the weather", "weather"),
            ("help me", "help"),
            ("how do I fix this?", "question"),
            ("some random text", "unknown"),
        ],
    )
    def test_detect_intent(self, message: str, expected: str):
        assert detect_intent(message) == expected


class TestGenerateResponse:
    def test_greeting_response(self):
        response = generate_response("hello", intent="greeting")
        assert "Hello" in response

    def test_weather_response(self):
        response = generate_response("weather", intent="weather")
        assert "weather" in response.lower() or "check" in response.lower()

    def test_unknown_response(self):
        response = generate_response("foobar", intent=None)
        assert "rephrase" in response.lower() or "understand" in response.lower()


class TestMainAgent:
    @pytest.mark.asyncio
    @patch("backend.agent.agent.load_session", new_callable=AsyncMock)
    @patch("backend.agent.agent.save_session", new_callable=AsyncMock)
    @patch("backend.agent.agent.log_interaction", new_callable=AsyncMock)
    async def test_new_session(self, mock_log, mock_save, mock_load):
        mock_load.return_value = None

        result = await main_agent("hello")

        assert "session_id" in result
        assert result["intent"] == "greeting"
        assert result["hint_level"] == 0
        assert "response" in result

        mock_save.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.agent.agent.load_session", new_callable=AsyncMock)
    @patch("backend.agent.agent.save_session", new_callable=AsyncMock)
    @patch("backend.agent.agent.log_interaction", new_callable=AsyncMock)
    async def test_repeat_triggers_hint(self, mock_log, mock_save, mock_load):
        # First call returns no session, second call returns session with repeat_count=1
        mock_load.side_effect = [None, {"hint_level": 0, "last_user_message": "hello", "last_ai_response": "Hi", "repeat_count": 1}]

        # First call creates session
        await main_agent("hello")
        # Second call should increase hint_level because repeat_count >= 2
        result = await main_agent("hello")

        assert result["hint_level"] == 1
        mock_save.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])