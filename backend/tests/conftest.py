# Test configuration
import os
import sys

# Set test environment variables
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "test_key")

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))