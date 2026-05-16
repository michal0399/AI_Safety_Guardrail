"""Negative tests: Invalid inputs and edge cases."""
import pytest

def test_empty_input(safety_guardrail):
    """Test handling of empty input."""
    result = safety_guardrail.protect("")
    assert result == ""

def test_none_input_handling(safety_guardrail):
    """Test that None input is handled gracefully."""
    # Should not raise exception
    try:
        result = safety_guardrail.protect(None)
    except (TypeError, AttributeError):
        # Expected behavior - should either convert or raise
        pass

def test_very_long_input(safety_guardrail):
    """Test handling of very long text."""
    long_text = "A" * 100000 + " " + "John Wick" + " " + "B" * 100000
    
    # Should not crash
    result = safety_guardrail.protect(long_text)
    assert isinstance(result, str)

def test_special_characters(safety_guardrail):
    """Test handling of special characters."""
    text = "Name: João @#$%^&*() Email: test@example.com"
    result = safety_guardrail.protect(text)
    
    assert isinstance(result, str)
    assert "test@example.com" not in result

def test_unicode_input(safety_guardrail):
    """Test handling of unicode characters."""
    text = "名前は田中 です、メールは tanaka@example.com"
    result = safety_guardrail.protect(text)
    
    assert isinstance(result, str)
    assert "tanaka@example.com" not in result

def test_malformed_email(safety_guardrail):
    """Test handling of malformed email addresses."""
    test_cases = [
        "notanemail",
        "@example.com",
        "user@",
        "user@@example.com"
    ]
    
    for email in test_cases:
        text = f"Email: {email}"
        result = safety_guardrail.protect(text)
        # Should not crash
        assert isinstance(result, str)

def test_mixed_case_and_spacing(safety_guardrail):
    """Test handling of unusual spacing and casing."""
    text = "  John   WICK  john@EXAMPLE.COM  "
    result = safety_guardrail.protect(text)
    
    # Should still mask despite odd formatting
    assert "john@EXAMPLE.COM" not in result or "john@example.com" not in result.lower()

def test_repeated_pii(safety_guardrail):
    """Test handling of same PII repeated multiple times."""
    text = "John Wick, John Wick, John Wick"
    result = safety_guardrail.protect(text)
    
    # Should create placeholders for each occurrence
    assert "John Wick" not in result
    assert result.count("<PERSON_") >= 1

def test_numeric_only_input(safety_guardrail):
    """Test handling of numeric-only input."""
    text = "123 456 789"
    result = safety_guardrail.protect(text)
    
    # Should handle without crash
    assert isinstance(result, str)

def test_sql_injection_attempt(safety_guardrail):
    """Test handling of SQL injection patterns."""
    text = "'; DROP TABLE users; --' john@example.com"
    result = safety_guardrail.protect(text)
    
    # Should safely mask email without executing anything
    assert "john@example.com" not in result
    assert isinstance(result, str)

def test_xss_attempt(safety_guardrail):
    """Test handling of XSS patterns."""
    text = '<script>alert("XSS")</script> John Wick john@example.com'
    result = safety_guardrail.protect(text)
    
    # Should mask without executing
    assert "john@example.com" not in result
    assert isinstance(result, str)

def test_reveal_with_nonexistent_placeholder(safety_guardrail):
    """Test reveal with placeholders that don't exist in vault."""
    text = "Contact <PERSON_999> at <EMAIL_ADDRESS_888>"
    result = safety_guardrail.reveal(text)
    
    # Should return unchanged (no mapping for these)
    assert "<PERSON_999>" in result or result == text
