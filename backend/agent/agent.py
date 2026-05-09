"""Learning Agent - Phase 1: Intelligent Response Strategy System

This is the core of your "AI Learning Tutor" - replaces simple hint levels with
adaptive teaching strategies that control AI behavior.

Teaching Modes:
- EXPLAINER: Direct explanations for new concepts
- TUTOR: Socratic method - asks questions before answering
- PRACTICE: Generates problems to solve
- DISCOVERY: Guided exploration

Hint Levels (now Learning Levels):
- 0 (NOVICE): Direct answer + explanation
- 1 (LEARNER): Ask what they think first + hints
- 2 (PRACTICER): Give practice problems
- 3 (MASTER): Challenge questions
"""

from typing import Dict, Any, List, Optional
import uuid
import datetime as dt

from sessions.redis_session import load_session, save_session
from database.mongodb import log_interaction
from services.ai_service import generate_response as ai_generate_response
from services.error_handling import handle_ai_error, validate_message, get_fallback_response, check_rate_limit


# ============== TEACHING STRATEGIES ==============

TEACHING_MODES = {
    "EXPLAINER": {
        "description": "Direct explanations for new concepts",
        "system_prompt": """You are an expert tutor who gives clear, direct explanations.
- Start with the core concept
- Use simple language
- Give 1-2 examples
- Keep it concise (2-3 paragraphs max)""",
    },
    "TUTOR": {
        "description": "Socratic method - guide through questions",
        "system_prompt": """You are a Socratic tutor who helps students discover answers themselves.
- NEVER give direct answers
- Ask guiding questions instead
- Break problem into smaller steps
- Ask "What do you think?" or "How would you approach this?"
- Lead them to discover the answer""",
    },
    "PRACTICE": {
        "description": "Generate practice problems",
        "system_prompt": """You are a practice problem generator.
- First briefly acknowledge their question
- Then generate 1-2 practice problems at appropriate difficulty
- Include the solution hidden (marked)
- Encourage them to try first""",
    },
    "DISCOVERY": {
        "description": "Guided exploration and discovery",
        "system_prompt": """You guide students through discovery-based learning.
- Present a scenario or puzzle
- Ask them to explore and hypothesize
- Give gentle nudges without full answers
- Help them reach conclusions themselves""",
    }
}


# Learning level to mode mapping
LEARNING_MODE_MAP = {
    0: "EXPLAINER",  # New user = direct
    1: "TUTOR",     # Need guidance = Socratic
    2: "PRACTICE",    # Need practice = problems
    3: "DISCOVERY",   # Advanced = discovery
}


# ============== HELPER FUNCTIONS ==============

def determine_learning_level(session: dict) -> int:
    """Determine user's learning level based on session data."""
    # Base on message count + correctness
    messages_count = session.get("messages_count", 0)
    correct_streak = session.get("correct_streak", 0)
    struggle_count = session.get("struggle_count", 0)
    
    # New user starts at level 0
    if messages_count < 3:
        return 0
    
    # If struggling often, lower level
    if struggle_count > 3:
        return max(0, (session.get("hint_level", 0) - 1))
    
    # If doing well consistently, increase level
    if correct_streak > 5:
        return min(3, (session.get("hint_level", 0) + 1))
    
    # Maintain current level
    return session.get("hint_level", 0)


def get_teaching_strategy(learning_level: int, message: str) -> tuple[str, str]:
    """Get teaching mode and system prompt based on learning level.
    
    Returns:
        (teaching_mode, system_prompt)
    """
    mode = LEARNING_MODE_MAP.get(learning_level, "EXPLAINER")
    strategy = TEACHING_MODES[mode]
    
    # Check if it's a quick question vs learning topic
    quick_questions = ["what is", "define", "explain", "who is", "when did"]
    is_quick = any(q in message.lower() for q in quick_questions)
    
    # Quick factual questions = direct mode regardless
    if is_quick and learning_level == 0:
        mode = "EXPLAINER"
        strategy = TEACHING_MODES[mode]
    
    return mode, strategy["system_prompt"]


def analyze_struggle(session: dict, message: str) -> dict:
    """Analyze if user is struggling and return intervention data."""
    prev_message = session.get("last_user_message", "")
    repeat_count = session.get("repeat_count", 0)
    struggle_count = session.get("struggle_count", 0)
    
    is_repeating = prev_message and (message.strip().lower() == prev_message.strip().lower())
    is_similar_question = False  # Could add NLP here
    
    return {
        "is_struggling": is_repeating or is_similar_question or struggle_count > 2,
        "repeat_count": repeat_count + 1 if is_repeating else 0,
        "struggle_indicator": struggle_count,
    }


# ============== MAIN AGENT ==============

async def main_agent(message: str, session_id: str | None = None) -> Dict[str, Any]:
    """Main learning agent with intelligent response strategy.
    
    Features:
    - Adaptive learning level based on user progress
    - Teaching mode selection based on learning level
    - Progress tracking
    - Struggle detection
    - Analytics logging
    - Error handling
    - Rate limiting
    
    Returns:
        dict with: session_id, intent, response, learning_level, teaching_mode, strategy
    """
    # ===== 0. VALIDATE INPUT =====
    is_valid, error_msg = validate_message(message)
    if not is_valid:
        return {
            "session_id": session_id or str(uuid.uuid4()),
            "intent": "validation_error",
            "response": error_msg,
            "learning_level": 0,
            "teaching_mode": "EXPLAINER",
            "strategy": "Input validation",
            "topic": "error",
            "messages_count": 0,
            "conversation_turns": 0,
            "error": error_msg,
        }
    
    # ===== 0b. RATE LIMITING =====
    # Use session_id or IP as identifier
    identifier = session_id or "anonymous"
    is_allowed, rate_msg = check_rate_limit(identifier)
    
    if not is_allowed:
        return {
            "session_id": identifier,
            "intent": "rate_limit",
            "response": rate_msg,
            "learning_level": 0,
            "teaching_mode": "EXPLAINER",
            "strategy": "Rate limiting",
            "topic": "error",
            "messages_count": 0,
            "conversation_turns": 0,
            "error": "rate_limit_exceeded",
        }
    
    # ===== 1. LOAD OR CREATE SESSION =====
    if session_id:
        sess = await load_session(session_id)
        if sess:
            session_id = session_id
        else:
            session_id = str(uuid.uuid4())
            sess = _create_new_session()
    else:
        session_id = str(uuid.uuid4())
        sess = _create_new_session()
    
    # ===== 2. ANALYZE STRUGGLE =====
    struggle_data = analyze_struggle(sess, message)
    
    # Update struggle count
    if struggle_data["is_struggling"]:
        sess["struggle_count"] = sess.get("struggle_count", 0) + 1
        sess["repeat_count"] = struggle_data["repeat_count"]
    else:
        sess["struggle_count"] = 0
        sess["repeat_count"] = 0
    
    # ===== 3. DETERMINE LEARNING LEVEL =====
    learning_level = determine_learning_level(sess)
    sess["learning_level"] = learning_level
    
    # ===== 4. GET TEACHING STRATEGY =====
    teaching_mode, system_prompt = get_teaching_strategy(learning_level, message)
    sess["teaching_mode"] = teaching_mode
    
    # ===== 5. BUILD CONVERSATION HISTORY =====
    # Get last messages for context (last 15 messages = ~8 turns)
    history = []
    if sess.get("message_history"):
        # Take last 15 messages for better context
        history = sess["message_history"][-15:]
    
    # Format history for AI - convert to conversation format
    formatted_history = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "assistant"
        formatted_history.append({
            "role": role,
            "content": msg.get("content", "")
        })
    
    # ===== 6. GENERATE AI RESPONSE =====
    try:
        # Build context summary for AI
        context_summary = f"""
User's Learning Level: {learning_level}/3
Topic: {sess.get('current_topic', 'general')}
Questions Asked: {sess.get('messages_count', 0)}
This Session: {sess.get('struggle_count', 0)} similar questions

{'Recent conversation:' if formatted_history else 'This is the start of the conversation.'}
{_format_history_for_ai(formatted_history) if formatted_history else ''}

Current question: {message}
"""
        
        full_system = f"""{system_prompt}

{context_summary}

Guidelines:
- Consider the conversation history
- Match teaching style to learning level
- Be encouraging
- Don't reveal answers unless in PRACTICE mode"""

        ai_response = await ai_generate_response(
            user_message=message,
            conversation_history=formatted_history,
            system_prompt=full_system
        )
    except Exception as e:
        # Handle AI errors gracefully with fallback
        error_response = await handle_ai_error(e)
        ai_response = error_response
    
    reply = ai_response
    
    # ===== 7. UPDATE SESSION DATA =====
    # Update message history
    current_history = sess.get("message_history", [])
    current_history.append({"role": "user", "content": message})
    current_history.append({"role": "assistant", "content": reply})
    # Keep last 10 messages
    sess["message_history"] = current_history[-10:]
    
    # Update counters
    sess["messages_count"] = sess.get("messages_count", 0) + 1
    sess["last_user_message"] = message
    sess["last_ai_response"] = reply
    sess["current_topic"] = _extract_topic(message)
    
    # ===== 8. SAVE SESSION =====
    await save_session(session_id, sess, ttl_days=7)
    
    # ===== 9. LOG INTERACTION =====
    try:
        await log_interaction(
            session_id=session_id,
            user_message=message,
            ai_response=reply,
            hint_level=learning_level,
            timestamp=dt.datetime.utcnow(),
            intent=teaching_mode,  # Log strategy used instead of raw intent
        )
    except Exception:
        pass
    
    # ===== 10. RETURN RESPONSE =====
    return {
        "session_id": session_id,
        "intent": teaching_mode,
        "response": reply,
        "learning_level": learning_level,
        "teaching_mode": teaching_mode,
        "strategy": TEACHING_MODES[teaching_mode]["description"],
        "topic": sess.get("current_topic", "general"),
        "messages_count": sess.get("messages_count", 0),
        "conversation_turns": len(formatted_history) // 2 if formatted_history else 0,
    }


def _create_new_session() -> dict:
    """Create a new learning session."""
    return {
        "learning_level": 0,
        "hint_level": 0,
        "teaching_mode": "EXPLAINER",
        "messages_count": 0,
        "message_history": [],
        "last_user_message": None,
        "last_ai_response": None,
        "current_topic": "general",
        "struggle_count": 0,
        "repeat_count": 0,
        "correct_streak": 0,
    }


def _extract_topic(message: str) -> str:
    """Simple topic extraction - can be enhanced with NLP."""
    message = message.lower()
    
    topics = {
        "programming": ["code", "python", "java", "javascript", "programming"],
        "math": ["calculate", "equation", "formula", "math"],
        "science": ["science", "physics", "chemistry", "biology"],
        "history": ["history", "when", "year", "century"],
        "language": ["grammar", "language", "syntax", "words"],
    }
    
    for topic, keywords in topics.items():
        if any(kw in message for kw in keywords):
            return topic
    
    return "general"


# Backwards compatibility - expose detect_intent for any legacy code
def detect_intent(message: str) -> str:
    """Legacy intent detection - now returns teaching mode."""
    _, system_prompt = get_teaching_strategy(0, message)
    # Return the teaching mode as "intent"
    return "learning_interaction"


# ============== HELPER FUNCTIONS ==============

def _format_history_for_ai(history: list) -> str:
    """Format conversation history for AI context display."""
    if not history:
        return ""
    
    lines = []
    for msg in history[-10:]:  # Last 10 messages
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:200]  # Truncate long messages
        lines.append(f"{role}: {content}")
    
    return "\n".join(lines)