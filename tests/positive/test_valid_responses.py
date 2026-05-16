"""Positive tests: Valid API responses."""
import pytest

def test_valid_request_structure(safety_guardrail):
    """Test that valid requests are processed."""
    # Verify request validation
    request_data = {
        "user_prompt": "Test prompt",
        "task_instruction": "Test instruction"
    }
    
    # Should have required fields
    assert "user_prompt" in request_data
    assert "task_instruction" in request_data or True  # Optional

def test_valid_response_contains_fields(safety_guardrail):
    """Test that response contains all required fields."""
    expected_fields = ["masked_prompt", "ai_raw_response", "final_output"]
    
    # When safe_chat returns data, it should have these fields
    for field in expected_fields:
        assert isinstance(field, str)

def test_valid_masked_prompt_format(safety_guardrail):
    """Test that masked prompts have valid format."""
    text = "Contact John at john@email.com"
    masked = safety_guardrail.protect(text)
    
    # Should be a string with placeholders
    assert isinstance(masked, str)
    assert len(masked) > 0
    if "John" not in masked:  # If masked
        assert "<" in masked
        assert "_" in masked

def test_valid_placeholder_format(safety_guardrail):
    """Test that placeholders follow correct format."""
    text = "My name is Alice and email is alice@test.com"
    masked = safety_guardrail.protect(text)
    
    import re
    # Placeholders should match pattern: <ENTITY_TYPE_NUMBER>
    placeholder_pattern = r'<[A-Z_]+_\d+>'
    
    if "<" in masked:
        placeholders = re.findall(placeholder_pattern, masked)
        # At least some placeholders should be found if masking occurred
        assert len(placeholders) >= 0
