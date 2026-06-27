import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from backend.agent.agent import main_agent
from backend.services.error_handling import check_rate_limit
from backend.services.auth_service import get_user_from_token
from backend.services.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify JWT token."""
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


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
    error: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """Learning chat endpoint with error handling and rate limiting."""
    # Check rate limit (simple IP-based)
    client_ip = request.client.host if request.client else "anonymous"
    is_allowed, rate_msg = check_rate_limit(client_ip)
    
    if not is_allowed:
        return ChatResponse(
            reply=rate_msg,
            session_id=req.session_id or "rate-limited",
            intent="rate_limit",
            learning_level=0,
            teaching_mode="EXPLAINER",
            strategy="Rate limiting",
            topic="error",
            messages_count=0,
            conversation_turns=0,
            error="rate_limit_exceeded",
        )
    
    # Process message
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
        error = result.get("error")
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
        error = None
    
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
        error=error,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """Stream AI response token-by-token via Server-Sent Events."""
    from backend.agent.agent import (
        determine_learning_level,
        get_teaching_strategy,
        analyze_struggle,
        _create_new_session,
        _extract_topic,
    )
    from backend.sessions.redis_session import load_session, save_session
    from backend.services.ai_service import generate_response_stream
    import uuid
    import datetime as dt

    session_id = req.session_id or str(uuid.uuid4())
    sess = await load_session(session_id)
    if not sess:
        sess = _create_new_session()

    struggle_data = analyze_struggle(sess, req.message)
    if struggle_data["is_struggling"]:
        sess["struggle_count"] = sess.get("struggle_count", 0) + 1
    else:
        sess["struggle_count"] = 0

    learning_level = determine_learning_level(sess)
    teaching_mode, system_prompt = get_teaching_strategy(learning_level, req.message)

    history = []
    if sess.get("message_history"):
        history = sess["message_history"][-15:]

    formatted_history = [
        {"role": "user" if m.get("role") == "user" else "assistant", "content": m.get("content", "")}
        for m in history
    ]

    async def event_stream():
        full_response = []
        try:
            yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id, 'teaching_mode': teaching_mode, 'learning_level': learning_level})}\n\n"

            async for chunk in generate_response_stream(
                user_message=req.message,
                conversation_history=formatted_history,
                system_prompt=system_prompt,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            reply = "".join(full_response)

            sess["message_history"] = (sess.get("message_history", []) + [
                {"role": "user", "content": req.message},
                {"role": "assistant", "content": reply},
            ])[-10:]
            sess["messages_count"] = sess.get("messages_count", 0) + 1
            sess["last_user_message"] = req.message
            sess["current_topic"] = _extract_topic(req.message)
            sess["learning_level"] = learning_level
            sess["teaching_mode"] = teaching_mode

            await save_session(session_id, sess, ttl_days=7)

            yield f"data: {json.dumps({'type': 'done', 'messages_count': sess['messages_count']})}\n\n"
        except Exception as e:
            logger.error("Streaming error for session %s: %s", session_id, e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
async def get_teaching_modes(user: dict = Depends(get_current_user)):
    """Get available teaching modes."""
    from backend.agent.agent import TEACHING_MODES
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
async def get_session_progress(session_id: str, user: dict = Depends(get_current_user)):
    """Get progress for a specific session."""
    from backend.sessions.redis_session import load_session

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


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    skip: int = 0,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """Get paginated chat history for a session from MongoDB interaction logs."""
    from backend.database.mongodb import get_collection

    limit = min(limit, 100)

    coll = await get_collection()
    if coll is None:
        return {"messages": [], "total": 0, "error": "Database unavailable"}

    cursor = coll.find({"session_id": session_id}).sort("timestamp", 1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    total = await coll.count_documents({"session_id": session_id})

    messages = [
        {
            "user_message": doc.get("user_message", ""),
            "ai_response": doc.get("ai_response", ""),
            "timestamp": doc.get("timestamp").isoformat() if doc.get("timestamp") else None,
            "teaching_mode": doc.get("intent"),
            "learning_level": doc.get("hint_level"),
        }
        for doc in docs
    ]

    return {
        "session_id": session_id,
        "messages": messages,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from backend.services.ai_service import is_configured
    
    return {
        "status": "ok",
        "ai_configured": is_configured(),
    }
