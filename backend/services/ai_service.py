"""Unified AI Service - automatically uses available AI provider.

Priority order:
1. Groq (fastest, free)
2. Gemini (Google)
3. Ollama (local, free)
4. Fallback (dummy)

Just set one API key in .env and it works!
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Default models
GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.0-flash"


async def generate_response(
    user_message: str,
    conversation_history: Optional[list] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """Generate AI response - auto-detects available provider.
    
    Args:
        user_message: The current user message
        conversation_history: Optional list of previous messages
        system_prompt: Optional system instructions
    
    Returns:
        AI response string
    """
    # 1. Try Groq (fastest, highest priority)
    if GROQ_API_KEY and GROQ_API_KEY not in ("", "your_groq_api_key_here"):
        try:
            result = await _groq_generate(user_message, conversation_history, system_prompt)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            pass  # Fall through to next provider
    
    # 2. Try Gemini
    if GEMINI_API_KEY and GEMINI_API_KEY not in ("", "your_gemini_api_key_here"):
        try:
            result = await _gemini_generate(user_message, system_prompt)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            pass  # Fall through to next provider
    
    # 3. Try Ollama (local)
    if OLLAMA_URL:
        try:
            result = await _ollama_generate(user_message, system_prompt)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            pass  # Fall through to fallback
    
    # 4. Fallback response
    return _fallback_response(user_message)


async def _groq_generate(user_message: str, history: Optional[list], system_prompt: Optional[str]) -> str:
    """Generate response using Groq API."""
    from groq import AsyncGroq
    
    client = AsyncGroq(api_key=GROQ_API_KEY)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        for msg in history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    messages.append({"role": "user", "content": user_message})
    
    chat_completion = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    
    if chat_completion.choices:
        return chat_completion.choices[0].message.content
    return "Error: No response from Groq"


async def _gemini_generate(user_message: str, system_prompt: Optional[str]) -> str:
    """Generate response using Gemini API."""
    try:
        from google import genai
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        full_prompt = user_message
        if system_prompt:
            full_prompt = system_prompt + "\n\n" + user_message
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )
        
        if response.text:
            return response.text
        return "Error: No response from Gemini"
    except Exception as e:
        return f"Error: {str(e)}"


async def _ollama_generate(user_message: str, system_prompt: Optional[str]) -> str:
    """Generate response using Ollama (local)."""
    import httpx
    
    full_prompt = user_message
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{user_message}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": "llama3", "prompt": full_prompt, "stream": False},
            timeout=30.0,
        )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("response", "").strip()
    return "Error: Ollama not available"


def _fallback_response(message: str) -> str:
    """Fallback dummy response when no AI provider is available."""
    m = (message or "").lower()
    if any(g in m for g in ["hello", "hi", "hey"]):
        return "Hello! How can I help you today?"
    if "?" in message:
        return "That's an interesting question. I'm currently without AI access, but I'd love to help if you configure an API key in the .env file!"
    return "I received your message! Configure a Groq or Gemini API key in the .env file for AI responses."


# Provider info functions
def get_provider() -> str:
    """Return the active AI provider name."""
    if GROQ_API_KEY and GROQ_API_KEY not in ("", "your_groq_api_key_here"):
        return "Groq"
    if GEMINI_API_KEY and GEMINI_API_KEY not in ("", "your_gemini_api_key_here"):
        return "Gemini"
    if OLLAMA_URL:
        return "Ollama"
    return "Fallback (no API key)"


def is_configured() -> bool:
    """Check if any AI provider is configured."""
    return bool(GROQ_API_KEY and GROQ_API_KEY not in ("", "your_groq_api_key_here")) or \
           bool(GEMINI_API_KEY and GEMINI_API_KEY not in ("", "your_gemini_api_key_here")) or \
           bool(OLLAMA_URL)