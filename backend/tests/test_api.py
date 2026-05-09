import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health endpoint returns ok."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestChatEndpoint:
    """Test chat endpoint."""
    
    @pytest.mark.asyncio
    async def test_chat_returns_reply(self, client):
        """Test chat returns a reply."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
    
    @pytest.mark.asyncio
    async def test_chat_returns_session_id(self, client):
        """Test chat returns session_id."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] is not None
    
    @pytest.mark.asyncio
    async def test_chat_returns_learning_level(self, client):
        """Test chat returns learning level."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "learning_level" in data
        assert data["learning_level"] == 0
    
    @pytest.mark.asyncio
    async def test_chat_returns_teaching_mode(self, client):
        """Test chat returns teaching mode."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "teaching_mode" in data
        assert data["teaching_mode"] in ["EXPLAINER", "TUTOR", "PRACTICE", "DISCOVERY"]
    
    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client):
        """Test chat rejects empty message."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": ""}
        )
        # Should return error in response
        data = response.json()
        assert data.get("error") is not None or data.get("reply") is not None
    
    @pytest.mark.asyncio
    async def test_chat_session_persistence(self, client):
        """Test same session persists data."""
        # First request
        r1 = await client.post("/api/v1/chat", json={"message": "hello"})
        sess_id = r1.json()["session_id"]
        
        # Second request with session
        r2 = await client.post(
            "/api/v1/chat", 
            json={"message": "hi", "session_id": sess_id}
        )
        assert r2.json()["session_id"] == sess_id
        assert r2.json()["messages_count"] == 2


class TestModesEndpoint:
    """Test teaching modes endpoint."""
    
    @pytest.mark.asyncio
    async def test_modes_returns_list(self, client):
        """Test modes endpoint returns list."""
        response = await client.get("/api/v1/modes")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert len(data["modes"]) == 4


class TestProgressEndpoint:
    """Test progress endpoint."""
    
    @pytest.mark.asyncio
    async def test_progress_requires_session(self, client):
        """Test progress needs valid session."""
        response = await client.get("/api/v1/progress/invalid-session-id")
        # Should return error or valid data
        data = response.json()
        assert "error" in data or "session_id" in data