from fastapi import APIRouter
from pydantic import BaseModel

from ....services.dummy_ai import generate_reply

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Generate a dummy AI reply using the service layer
    reply = generate_reply(req.message)
    return ChatResponse(reply=reply)
