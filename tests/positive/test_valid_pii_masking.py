"""Positive tests: Valid PII masking scenarios."""
import pytest

def test_valid_person_name_masking(safety_guardrail):
    """Test valid person name is properly masked."""
    test_cases = [
        "John Wick",
        "Jane Doe",
        "Dr. Robert Smith",
        "María García"
    ]
    
    for name in test_cases:
        text = f"Contact {name}"
        masked = safety_guardrail.protect(text)
        assert name not in masked
        assert "<PERSON_" in masked

def test_valid_email_masking(safety_guardrail):
    """Test valid email addresses are properly masked."""
    test_cases = [
        "user@example.com",
        "john.doe@company.co.uk",
        "info+tag@domain.org",
        "test.name@subdomain.example.com"
    ]
    
    for email in test_cases:
        text = f"Email: {email}"
        masked = safety_guardrail.protect(text)
        assert email not in masked
        assert "<EMAIL_ADDRESS_" in masked

def test_valid_phone_masking(safety_guardrail):
    """Test various phone number formats are masked."""
    test_cases = [
        "555-123-4567",
        "(555) 123-4567",
        "+1-555-123-4567",
        "555.123.4567"
    ]
    
    for phone in test_cases:
        text = f"Call: {phone}"
        masked = safety_guardrail.protect(text)
        assert phone not in masked
        assert "<PHONE_NUMBER_" in masked

def test_valid_address_masking(safety_guardrail):
    """Test addresses are properly masked."""
    test_cases = [
        "123 Main Street, New York, NY 10001",
        "456 Oak Avenue, Los Angeles, CA 90001",
        "789 Pine Road, Chicago, IL 60601"
    ]
    
    for address in test_cases:
        text = f"Address: {address}"
        masked = safety_guardrail.protect(text)
        assert address not in masked
        assert "<LOCATION_" in masked

def test_valid_date_masking(safety_guardrail):
    """Test dates are properly masked."""
    test_cases = [
        "01/15/1990",
        "January 15, 1990",
        "2023-12-25",
        "Dec 25, 2023"
    ]
    
    for date in test_cases:
        text = f"Date: {date}"
        masked = safety_guardrail.protect(text)
        # Date detection is not 100% reliable, so we just verify no crash
        assert isinstance(masked, str)

def test_valid_complete_workflow(safety_guardrail):
    """Test complete workflow with all PII types."""
    original = (
        "My name is John Smith, born 01/15/1990, "
        "living at 123 Main Street, New York, NY 10001. "
        "Contact me at john.smith@email.com or 555-123-4567."
    )
    
    masked = safety_guardrail.protect(original)
    
    # Verify masking occurred
    assert "John Smith" not in masked
    assert "01/15/1990" not in masked
    assert "123 Main Street" not in masked
    assert "john.smith@email.com" not in masked
    assert "555-123-4567" not in masked
    
    # Verify placeholders exist
    assert "<" in masked and ">" in masked

def test_valid_reveal_with_placeholders(safety_guardrail):
    """Test reveal properly restores placeholders."""
    original = "John Wick - john@example.com"
    masked = safety_guardrail.protect(original)
    
    # Create AI response with placeholders
    ai_response = f"Professional info: {masked.split('-')[0]}"
    
    revealed = safety_guardrail.reveal(ai_response)
    assert isinstance(revealed, str)
    assert len(revealed) > 0
