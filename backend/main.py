import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Allow multiple origins for development and production
origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://thinkspire.vercel.app",  # Vercel frontend
]

# If FRONTEND_URL is set, add it as well
if FRONTEND_URL not in origins:
    origins.append(FRONTEND_URL)

app = FastAPI(title="Think-Inspire Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.v1.routers.chat import router as chat_router
from api.v1.routers.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1", tags=["v1"])


@app.get("/health")
async def health_check():
    from services.ai_service import is_configured
    return JSONResponse({
        "status": "ok", 
        "ai_configured": is_configured(),
        "frontend_url": FRONTEND_URL,
        "cors_origins": origins,
    })


@app.on_event("shutdown")
async def shutdown_event():
    from sessions.redis_session import close_client
    await close_client()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)