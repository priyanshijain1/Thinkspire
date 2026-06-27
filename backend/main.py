import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from backend.services.logging_config import setup_logging, get_logger

BACKEND_DIR = Path(__file__).parent
load_dotenv(BACKEND_DIR / ".env")

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://thinkspire.vercel.app",
]

app = FastAPI(title="Think-Inspire Backend")


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """Add request ID to every request for distributed tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.v1.routers.chat import router as chat_router
from backend.api.v1.routers.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1", tags=["v1"])


@app.get("/health")
async def health_check():
    from backend.services.ai_service import is_configured
    return JSONResponse({
        "status": "ok",
        "ai_configured": is_configured(),
    })


@app.on_event("shutdown")
async def shutdown_event():
    from backend.sessions.redis_session import close_client
    await close_client()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
