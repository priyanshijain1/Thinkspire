import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDetectIntent:
    """Test intent detection."""
    
    def test_greeting_intent(self):
        """Test greeting detection."""
        from backend.agent.agent import detect_intent
        assert detect_intent("hello") == "learning_interaction"
        assert detect_intent("hi there") == "learning_interaction"
    
    def test_question_intent(self):
        """Test question detection."""
        from backend.agent.agent import detect_intent
        result = detect_intent("what is python?")
        assert result == "learning_interaction"


class TestTeachingModes:
    """Test teaching modes configuration."""
    
    def test_teaching_modes_exist(self):
        """Test all teaching modes are defined."""
        from backend.agent.agent import TEACHING_MODES
        assert "EXPLAINER" in TEACHING_MODES
        assert "TUTOR" in TEACHING_MODES
        assert "PRACTICE" in TEACHING_MODES
        assert "DISCOVERY" in TEACHING_MODES
    
    def test_teaching_mode_descriptions(self):
        """Test teaching modes have descriptions."""
        from backend.agent.agent import TEACHING_MODES
        for mode, config in TEACHING_MODES.items():
            assert "description" in config
            assert "system_prompt" in config
    
    def test_learning_mode_map(self):
        """Test learning level mapping."""
        from backend.agent.agent import LEARNING_MODE_MAP
        assert LEARNING_MODE_MAP[0] == "EXPLAINER"
        assert LEARNING_MODE_MAP[1] == "TUTOR"
        assert LEARNING_MODE_MAP[2] == "PRACTICE"
        assert LEARNING_MODE_MAP[3] == "DISCOVERY"


class TestExtractTopic:
    """Test topic extraction."""
    
    def test_programming_topic(self):
        """Test programming topic detection."""
        from backend.agent.agent import _extract_topic
        assert _extract_topic("how to write python code") == "programming"
        assert _extract_topic("javascript function") == "programming"
    
    def test_math_topic(self):
        """Test math topic detection."""
        from backend.agent.agent import _extract_topic
        assert _extract_topic("calculate this equation") == "math"
        assert _extract_topic("what is the formula") == "math"
    
    def test_general_topic(self):
        """Test general topic default."""
        from backend.agent.agent import _extract_topic
        assert _extract_topic("random text") == "general"


class TestValidation:
    """Test input validation."""
    
    def test_valid_message(self):
        """Test valid message passes."""
        from backend.services.error_handling import validate_message
        is_valid, error = validate_message("Hello world")
        assert is_valid is True
        assert error is None
    
    def test_empty_message(self):
        """Test empty message fails."""
        from backend.services.error_handling import validate_message
        is_valid, error = validate_message("")
        assert is_valid is False
        assert error is not None
    
    def test_too_short_message(self):
        """Test too short message fails."""
        from backend.services.error_handling import validate_message
        is_valid, error = validate_message("a")
        assert is_valid is False
    
    def test_too_long_message(self):
        """Test too long message fails."""
        from backend.services.error_handling import validate_message
        long_message = "a" * 6000
        is_valid, error = validate_message(long_message)
        assert is_valid is False


class TestRateLimiter:
    """Test rate limiting."""
    
    def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests under limit."""
        from backend.services.error_handling import RateLimiter
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Should allow first 10 requests
        for i in range(10):
            assert limiter.is_allowed("test_user") is True
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks over limit."""
        from backend.services.error_handling import RateLimiter
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # First 3 should pass
        assert limiter.is_allowed("test_user") is True
        assert limiter.is_allowed("test_user") is True
        assert limiter.is_allowed("test_user") is True
        
        # 4th should fail
        assert limiter.is_allowed("test_user") is False
    
    def test_different_users_separate_limits(self):
        """Test different users have separate limits."""
        from backend.services.error_handling import RateLimiter
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False  # user1 blocked
        
        # user2 should still be allowed
        assert limiter.is_allowed("user2") is True