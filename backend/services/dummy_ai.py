"""Simple dummy AI service used by the API to generate replies."""

def generate_reply(message: str) -> str:
    """Return a simple, deterministic reply based on the input message."""
    if not message:
        return "I didn't catch that. Could you repeat your message?"
    m = message.strip().lower()
    if any(word in m for word in ["hello", "hi", "hey"]):
        return "Hello! How can I assist you today?"
    if "weather" in m:
        return "I don't have live weather data right now, but I can show you how to check it."
    if "help" in m:
        return "Sure—tell me what you need help with and I'll do my best to assist."
    # Fallback echo with a bit of personality
    return f"You said: '{message}'. What would you like to discuss next?"
