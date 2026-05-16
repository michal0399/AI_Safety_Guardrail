"""Shared test fixtures and configurations."""
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def safety_guardrail():
    """Fixture to provide SafetyGuardrail instance."""
    from safety_guardrail.engine import SafetyGuardrail
    return SafetyGuardrail()

@pytest.fixture
def sample_pii_texts():
    """Fixture providing various PII text samples."""
    return {
        "person_email": "My name is John Wick and my email is boogeyman@continental.com",
        "phone_number": "Call me at 555-123-4567",
        "address": "I live at 123 Main Street, New York, NY 10001",
        "birthdate": "I was born on January 15, 1990",
        "complex_pii": "My name is Jane Doe, DOB: 03/20/1985, living at 456 Oak Ave, Los Angeles. Contact: jane.doe@email.com or (310) 555-9876",
        "no_pii": "The weather is nice today",
        "url": "Visit my website at https://www.example.com",
        "credit_card": "My card number is 4532-1234-5678-9010"
    }

@pytest.fixture
def mock_ai_response():
    """Fixture providing mock AI responses with placeholders."""
    return {
        "with_placeholders": "Here is a bio for <PERSON_0>. You can reach them at <EMAIL_ADDRESS_1>.",
        "without_placeholders": "Here is a professional bio.",
        "mixed": "Contact <PERSON_0> at <EMAIL_ADDRESS_1> or visit their office at <LOCATION_2>."
    }
