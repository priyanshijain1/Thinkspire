from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any

from ....agent.agent import main_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
    hint_level: Optional[int] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Connect to the new agent to determine intent and response, with session state
    result = main_agent(req.message, req.session_id)
    if isinstance(result, dict):
        reply = result.get("response")
        session_id = result.get("session_id")
        intent = result.get("intent")
        hint_level = result.get("hint_level")
    else:
        reply = str(result)
        session_id = req.session_id
        intent = None
        hint_level = None
    return ChatResponse(reply=reply, session_id=session_id, intent=intent, hint_level=hint_level)
