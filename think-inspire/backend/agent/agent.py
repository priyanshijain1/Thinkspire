"""Simple agent module for intent detection and response generation.

This is a non-AI placeholder to demonstrate the integration point
between the frontend and backend without relying on external services.
"""

from typing import Dict


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
        return "I can't fetch weather data yet, but I can guide you on how to check it."
    if intent == "help":
        return "Sure—tell me what you need help with and I'll assist."
    if intent == "question":
        return "I'll do my best to answer your question."
    return "I didn't understand that. Could you rephrase?"


def main_agent(message: str) -> Dict[str, str]:
    """Connect detect_intent and generate_response into a single entry point.

    Returns a dict with keys: intent, response
    """
    intent = detect_intent(message)
    response = generate_response(message, intent)
    return {"intent": intent, "response": response}
