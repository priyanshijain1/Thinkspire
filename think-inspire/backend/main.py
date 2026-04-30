from fastapi import FastAPI
from .api.v1.routers.chat import router as chat_router

app = FastAPI(title="Think-Inspire Backend")

# Register routers
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
