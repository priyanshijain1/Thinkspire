from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pathlib import Path
from .api.v1.routers.chat import router as chat_router

# Load .env from backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

app = FastAPI(title="Think-Inspire Backend")

# Allow local frontend (Next.js dev) to call this API
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})


@app.on_event("shutdown")
async def shutdown_event():
    from .sessions.redis_session import close_client
    await close_client()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
