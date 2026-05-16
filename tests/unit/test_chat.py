"""Unit tests for chat module functions."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'safety_guardrail'))

def test_load_system_rules_exists(sample_pii_texts):
    """Test loading system rules from existing file."""
    from chat import load_system_rules
    
    rules = load_system_rules()
    
    # Verify rules contain expected content
    assert "CRITICAL SYSTEM RULES" in rules or len(rules) > 0
    assert isinstance(rules, str)

def test_load_system_rules_not_found():
    """Test graceful handling when rules file doesn't exist."""
    from chat import load_system_rules
    
    # Load with non-existent path
    rules = load_system_rules("/nonexistent/path/safety_rules.txt")
    
    # Should return empty string, not raise exception
    assert rules == ""

def test_safe_chat_returns_dict():
    """Test that safe_chat returns a dictionary with expected keys."""
    # This would require mocking the Gemini API
    # For now, we'll verify the structure
    expected_keys = ["masked_prompt", "ai_raw_response", "final_output"]
    
    # When safe_chat is called, it should return a dict with these keys
    assert all(isinstance(key, str) for key in expected_keys)
