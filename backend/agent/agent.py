"""Simple agent module for intent detection and response generation.

This uses Gemini AI for intelligent responses.
Includes a Redis-backed hint system per session.
"""

from typing import Dict, Any, List
import uuid
import datetime as dt

from ..sessions.redis_session import load_session, save_session
from ..database.mongodb import log_interaction
from ..services.ai_service import generate_response as ai_generate_response


def detect_intent(message: str) -> str:
    m = (message or "").lower()
    if any(greet in m for greet in ["hello", "hi", "hey", "greetings"]):
        return "greeting"
    if "weather" in m:
        return "weather"
    if "help" in m:
        return "help"
    if "?" in message or m.endswith("?"):
        return "question"
    return "unknown"


def generate_response(message: str, intent: str = None) -> str:
    if not intent:
        intent = detect_intent(message)
    if intent == "greeting":
        return "Hello! How can I assist you today?"
    if intent == "weather":
        return "I can't fetch weather data yet, but I can show you how to check it."
    if intent == "help":
        return "Sure—tell me what you need help with and I'll assist."
    if intent == "question":
        return "I'll do my best to answer your question."
    return "I didn't understand that. Could you rephrase?"


async def main_agent(message: str, session_id: str | None = None) -> Dict[str, Any]:
    """Connect detect_intent and generate_response into a single entry point with hint state.

    Uses Redis for session state.
    Returns: dict with keys session_id, intent, response, hint_level
    """
    # Load session from Redis or create new
    if session_id:
        sess = await load_session(session_id)
        if sess:
            session_id = session_id
        else:
            session_id = str(uuid.uuid4())
            sess = {
                "hint_level": 0,
                "last_user_message": None,
                "last_ai_response": "",
                "repeat_count": 0,
            }
    else:
        session_id = str(uuid.uuid4())
        sess = {
            "hint_level": 0,
            "last_user_message": None,
            "last_ai_response": "",
            "repeat_count": 0,
        }

    # Track repeats to determine if user is stuck
    if (sess.get("last_user_message") or "") == (message or ""):
        sess["repeat_count"] = sess.get("repeat_count", 0) + 1
    else:
        sess["repeat_count"] = 0

    # Determine intent (optional - for analytics)
    intent = detect_intent(message)

    # Get AI response from Groq
    ai_response = await ai_generate_response(message)

    # Build response according to hint level (optional enhancement system)
    # For now, we use the AI response directly
    level = sess.get("hint_level", 0)

    # Use AI response as-is ( Gemini provides good responses)
    reply = ai_response

    # Persist last user message/response
    sess["last_user_message"] = message
    sess["last_ai_response"] = reply

    # Save updated session to Redis with TTL
    await save_session(session_id, sess, ttl_days=7)

    # Persist interaction to MongoDB (best effort, non-blocking)
    try:
        await log_interaction(session_id, message, reply, level, timestamp=dt.datetime.utcnow(), intent=intent)
    except Exception:
        pass

    return {
        "session_id": session_id,
        "intent": intent,
        "response": reply,
        "hint_level": level,
    }