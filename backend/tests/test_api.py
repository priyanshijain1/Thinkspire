import pytest
from httpx import AsyncClient, ASGITransport

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.main import app


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_returns_reply(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/chat",
                json={"message": "hello"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data
            assert "session_id" in data
            assert "intent" in data
            assert "hint_level" in data

    @pytest.mark.asyncio
    async def test_chat_persists_session(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request
            r1 = await client.post("/chat", json={"message": "hello"})
            sess_id = r1.json()["session_id"]

            # Second request with same session
            r2 = await client.post("/chat", json={"message": "hello", "session_id": sess_id})
            assert r2.json()["session_id"] == sess_id
            # Hint level may increase due to repeat detection
            assert r2.json()["hint_level"] >= 0

    @pytest.mark.asyncio
    async def test_chat_invalid_body(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/chat", json={"message": ""})
            # FastAPI validation rejects empty message
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])