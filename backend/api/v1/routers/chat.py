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
    learning_level: int = 0
    teaching_mode: str = "EXPLAINER"
    strategy: Optional[str] = None
    topic: str = "general"
    messages_count: int = 0
    conversation_turns: int = 0


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Learning chat endpoint with full conversation history."""
    result = await main_agent(req.message, req.session_id)
    
    if isinstance(result, dict):
        reply = result.get("response", "")
        session_id = result.get("session_id")
        intent = result.get("intent")
        learning_level = result.get("learning_level", 0)
        teaching_mode = result.get("teaching_mode", "EXPLAINER")
        strategy = result.get("strategy", "")
        topic = result.get("topic", "general")
        messages_count = result.get("messages_count", 0)
        conversation_turns = result.get("conversation_turns", 0)
    else:
        reply = str(result)
        session_id = req.session_id
        intent = None
        learning_level = 0
        teaching_mode = "EXPLAINER"
        strategy = None
        topic = "general"
        messages_count = 0
        conversation_turns = 0
    
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent,
        learning_level=learning_level,
        teaching_mode=teaching_mode,
        strategy=strategy,
        topic=topic,
        messages_count=messages_count,
        conversation_turns=conversation_turns,
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


@router.get("/progress/{session_id}")
async def get_session_progress(session_id: str):
    """Get progress for a specific session."""
    from ....sessions.redis_session import load_session
    
    session = await load_session(session_id)
    
    if not session:
        return {"error": "Session not found"}
    
    return {
        "session_id": session_id,
        "learning_level": session.get("learning_level", 0),
        "teaching_mode": session.get("teaching_mode", "EXPLAINER"),
        "messages_count": session.get("messages_count", 0),
        "current_topic": session.get("current_topic", "general"),
        "struggle_count": session.get("struggle_count", 0),
    }