from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ....agent.agent import main_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
    learning_level: Optional[int] = 0
    teaching_mode: Optional[str] = "EXPLAINER"
    strategy: Optional[str] = None
    topic: Optional[str] = "general"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Learning chat endpoint with intelligent response strategy."""
    result = await main_agent(req.message, req.session_id)
    
    if isinstance(result, dict):
        reply = result.get("response", "")
        session_id = result.get("session_id")
        intent = result.get("intent")
        learning_level = result.get("learning_level", 0)
        teaching_mode = result.get("teaching_mode", "EXPLAINER")
        strategy = result.get("strategy", "")
        topic = result.get("topic", "general")
    else:
        reply = str(result)
        session_id = req.session_id
        intent = None
        learning_level = 0
        teaching_mode = "EXPLAINER"
        strategy = None
        topic = "general"
    
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent,
        learning_level=learning_level,
        teaching_mode=teaching_mode,
        strategy=strategy,
        topic=topic
    )


@router.get("/modes")
async def get_teaching_modes():
    """Get available teaching modes."""
    from ....agent.agent import TEACHING_MODES
    return {
        "modes": [
            {
                "mode": key,
                "description": value["description"],
            }
            for key, value in TEACHING_MODES.items()
        ]
    }