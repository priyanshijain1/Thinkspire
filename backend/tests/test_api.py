import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_token(client):
    """Get JWT token for testing."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token):
    """Get auth headers with token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthEndpoint:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client):
        response = await client.post("/api/v1/chat", json={"message": "hello"})
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_chat_returns_reply(self, client, auth_headers):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "hello"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
    
    @pytest.mark.asyncio
    async def test_chat_returns_session_id(self, client, auth_headers):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "hello"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "session_id" in response.json()
    
    @pytest.mark.asyncio
    async def test_chat_returns_learning_level(self, client, auth_headers):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["learning_level"] == 0
    
    @pytest.mark.asyncio
    async def test_chat_returns_teaching_mode(self, client, auth_headers):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"},
            headers=auth_headers
        )
        assert response.status_code == 200
        mode = response.json()["teaching_mode"]
        assert mode in ["EXPLAINER", "TUTOR", "PRACTICE", "DISCOVERY"]
    
    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client, auth_headers):
        response = await client.post(
            "/api/v1/chat",
            json={"message": ""},
            headers=auth_headers
        )
        data = response.json()
        assert data.get("error") is not None or data.get("reply") is not None
    
    @pytest.mark.asyncio
    async def test_chat_session_persistence(self, client, auth_headers):
        r1 = await client.post("/api/v1/chat", json={"message": "hello"}, headers=auth_headers)
        sess_id = r1.json()["session_id"]
        
        r2 = await client.post(
            "/api/v1/chat",
            json={"message": "hi", "session_id": sess_id},
            headers=auth_headers
        )
        assert r2.json()["session_id"] == sess_id
        assert r2.json()["messages_count"] == 2


class TestModesEndpoint:
    @pytest.mark.asyncio
    async def test_modes_requires_auth(self, client):
        response = await client.get("/api/v1/modes")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_modes_returns_list(self, client, auth_headers):
        response = await client.get("/api/v1/modes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert len(data["modes"]) == 4


class TestProgressEndpoint:
    @pytest.mark.asyncio
    async def test_progress_requires_auth(self, client):
        response = await client.get("/api/v1/progress/test-session")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_progress_requires_session(self, client, auth_headers):
        response = await client.get("/api/v1/progress/invalid-session", headers=auth_headers)
        data = response.json()
        assert "error" in data or "session_id" in data