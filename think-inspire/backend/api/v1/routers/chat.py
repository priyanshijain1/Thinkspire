from fastapi import APIRouter
from pydantic import BaseModel

from ....agent.agent import main_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Connect to the new agent to determine intent and response
    result = main_agent(req.message)
    reply = result.get("response") if isinstance(result, dict) else str(result)
    return ChatResponse(reply=reply)
