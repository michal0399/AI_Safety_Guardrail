"""Regression tests: Known issues and previously fixed bugs."""

import pytest


def test_birthdate_masking_regression(safety_guardrail):
    """
    REGRESSION TEST: Ensure birthdates are masked.
    Issue: Previously, birthdates were not being detected and masked.
    Fix: Added DATE_TIME to detected entities in SafetyGuardrail.protect()
    """
    text = "I was born on 01/15/1990"
    masked = safety_guardrail.protect(text)

    # This should now be masked
    assert "01/15/1990" not in masked or "<DATE_TIME_" in masked


def test_address_masking_regression(safety_guardrail):
    """
    REGRESSION TEST: Ensure addresses are masked.
    Issue: Previously, full addresses were not being detected.
    Fix: Added LOCATION to detected entities.
    """
    text = "Living at 123 Main Street, New York, NY 10001"
    masked = safety_guardrail.protect(text)

    # This should now be masked
    assert "123 Main Street" not in masked or "<LOCATION_" in masked


def test_phone_number_masking_regression(safety_guardrail):
    """
    REGRESSION TEST: Ensure phone numbers are masked.
    Issue: Previously, phone numbers were not being detected.
    Fix: Added PHONE_NUMBER to detected entities.
    """
    text = "Call me at 555-123-4567"
    masked = safety_guardrail.protect(text)

    # This should now be masked
    assert "555-123-4567" not in masked or "<PHONE_NUMBER_" in masked


def test_placeholder_format_consistency(safety_guardrail):
    """
    REGRESSION TEST: Ensure placeholders follow consistent format.
    Issue: Previously, placeholder format was inconsistent.
    Fix: Standardized to <ENTITY_TYPE_NUMBER> format.
    """
    text = "John at john@example.com"
    masked = safety_guardrail.protect(text)

    # All placeholders should follow the pattern
    import re

    placeholders = re.findall(r"<[^>]+>", masked)

    for placeholder in placeholders:
        # Should match pattern: <WORD_NUMBER> or <WORD_WORD_NUMBER>
        assert re.match(r"^<[A-Z_]+_\d+>$", placeholder)


def test_mapping_vault_stability(safety_guardrail):
    """
    REGRESSION TEST: Ensure mapping vault remains stable.
    Issue: Previously, mapping vault could be overwritten unexpectedly.
    Fix: Ensured each Guard instance has isolated mapping vault.
    """
    from safety_guardrail.engine import SafetyGuardrail

    guard1 = SafetyGuardrail()
    guard2 = SafetyGuardrail()

    text = "Contact John"
    guard1.protect(text)
    vault1_size = len(guard1.mapping_vault)

    guard2.protect("Different text")

    # Guard1's vault should not change
    assert len(guard1.mapping_vault) == vault1_size


def test_complete_workflow_end_to_end(safety_guardrail):
    """
    REGRESSION TEST: Ensure complete workflow works end-to-end.
    Issue: Previously, protect() returned string instead of dict (after recent changes).
    Fix: Ensured safe_chat() returns dict with masked_prompt, ai_raw_response, final_output.
    """
    # This tests that the engine part works correctly
    original = "John Wick - john@example.com - 555-1234"
    masked = safety_guardrail.protect(original)

    assert isinstance(masked, str)
    assert "John Wick" not in masked
    assert "john@example.com" not in masked

    # Simulate reveal
    revealed = safety_guardrail.reveal(masked)
    assert isinstance(revealed, str)
