"""Error handling and fallback system for the learning agent."""

from typing import Dict, Any, Optional
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== ERROR TYPES ==============

class LearningAgentError(Exception):
    """Base exception for learning agent."""
    pass


class AIServiceError(LearningAgentError):
    """AI service unavailable."""
    pass


class SessionError(LearningAgentError):
    """Session-related errors."""
    pass


class ValidationError(LearningAgentError):
    """Input validation errors."""
    pass


# ============== ERROR HANDLERS ==============

async def handle_ai_error(error: Exception, fallback_message: str = None) -> str:
    """Handle AI service errors with fallback."""
    error_msg = str(error)
    
    logger.error(f"AI Error: {error_msg}")
    
    # Check if it's a specific error type
    if "429" in error_msg or "rate" in error_msg.lower():
        return "I'm getting rate-limited. Please wait a moment and try again."
    
    if "401" in error_msg or "auth" in error_msg.lower():
        return "AI service authentication failed. Please check API keys."
    
    if "timeout" in error_msg.lower():
        return "The AI is taking too long to respond. Please try again."
    
    if "connection" in error_msg.lower():
        return "Having trouble connecting to the AI service. Please try again."
    
    # Generic fallback
    if fallback_message:
        return fallback_message
    
    return "I'm having trouble generating a response right now. Could you try rephrasing your question?"


async def handle_session_error(error: Exception) -> Dict[str, Any]:
    """Handle session errors gracefully."""
    logger.error(f"Session Error: {str(error)}")
    
    return {
        "error": "Session error",
        "message": "There was an issue with your session. Starting a new one.",
        "recovery_action": "restart",
    }


def validate_message(message: str) -> tuple[bool, Optional[str]]:
    """Validate user message input."""
    if not message:
        return False, "Message cannot be empty"
    
    if not isinstance(message, str):
        return False, "Message must be a string"
    
    # Check length constraints
    if len(message.strip()) < 2:
        return False, "Message is too short"
    
    if len(message) > 5000:
        return False, "Message is too long (max 5000 characters)"
    
    return True, None


# ============== FALLBACK RESPONSES ==============

FALLBACK_RESPONSES = {
    "greeting": [
        "Hello! I'm your AI learning assistant. What would you like to learn about?",
        "Hi there! Ready to help you learn. What's your question?",
        "Hey! Great to have you here. What can I help you with today?",
    ],
    "default": [
        "I'm here to help you learn! Could you rephrase that?",
        "I'd love to help you with that. Can you give me more context?",
        "That sounds interesting! Tell me more about what you want to learn.",
    ],
    "struggling": [
        "It seems you're stuck on this. Let me know what specifically is confusing you?",
        "Let's break this down together. What part is most challenging?",
        "Don't worry, we'll figure this out! What have you tried so far?",
    ],
    "encouragement": [
        "Great question! Keep exploring and learning!",
        "You're on the right track! Keep asking questions.",
        "Learning takes practice. You're doing great!",
    ],
}


def get_fallback_response(category: str = "default") -> str:
    """Get a random fallback response from the pool."""
    import random
    
    responses = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES["default"])
    return random.choice(responses)


# ============== RATE LIMITING ==============

from collections import defaultdict
from datetime import datetime, timedelta

# Simple in-memory rate limiter
class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[key] = [
            req for req in self.requests[key]
            if req > cutoff
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add new request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        self.requests[key] = [
            req for req in self.requests[key]
            if req > cutoff
        ]
        
        return max(0, self.max_requests - len(self.requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


def check_rate_limit(identifier: str) -> tuple[bool, str]:
    """Check if request is within rate limits."""
    is_allowed = rate_limiter.is_allowed(identifier)
    
    if not is_allowed:
        remaining = 0
        return False, f"Rate limit exceeded. Try again in a moment. ({remaining} requests remaining)"
    
    remaining = rate_limiter.get_remaining(identifier)
    return True, f"{remaining} requests remaining this minute"