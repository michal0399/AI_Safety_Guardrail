"""Integration tests for the complete PII protection workflow."""

import pytest


def test_protect_and_reveal_workflow(safety_guardrail, sample_pii_texts):
    """Test the complete protect -> AI -> reveal workflow."""
    original_text = sample_pii_texts["complex_pii"]

    # Step 1: Protect
    masked_prompt = safety_guardrail.protect(original_text)
    assert "Jane Doe" not in masked_prompt
    assert "03/20/1985" not in masked_prompt
    assert "456 Oak Ave" not in masked_prompt
    assert "jane.doe@email.com" not in masked_prompt

    # Step 2: Simulate AI response with placeholders
    ai_response = f"Here's the bio for {masked_prompt.split(',')[0].split()[-1]}. Contact them via their email."

    # Step 3: Reveal
    final_output = safety_guardrail.reveal(ai_response)

    # Verify sensitive data is restored
    assert isinstance(final_output, str)


def test_workflow_isolation(safety_guardrail, sample_pii_texts):
    """Test that multiple workflows don't interfere with each other."""
    from safety_guardrail.engine import SafetyGuardrail

    guard1 = SafetyGuardrail()
    guard2 = SafetyGuardrail()

    text1 = sample_pii_texts["person_email"]
    text2 = sample_pii_texts["phone_number"]

    masked1 = guard1.protect(text1)
    masked2 = guard2.protect(text2)

    # Each guard should have independent mappings
    assert guard1.mapping_vault != guard2.mapping_vault

    # Reveal operations should use their own vaults
    assert guard1.reveal("test") == "test"
    assert guard2.reveal("test") == "test"


def test_concurrent_pii_detection(safety_guardrail, sample_pii_texts):
    """Test detecting multiple PII types in single text."""
    complex_text = (
        f"{sample_pii_texts['person_email']} "
        f"Phone: {sample_pii_texts['phone_number'].split('at ')[-1]} "
        f"Address: {sample_pii_texts['address']}"
    )

    masked = safety_guardrail.protect(complex_text)

    # Should detect all PII types
    assert "<PERSON_" in masked
    assert "<EMAIL_ADDRESS_" in masked
    assert "<PHONE_NUMBER_" in masked
    assert "<LOCATION_" in masked
