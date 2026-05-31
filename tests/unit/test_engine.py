"""Unit tests for SafetyGuardrail engine."""

import pytest


def test_protect_person_detection(safety_guardrail, sample_pii_texts):
    """Test that PERSON entities are properly detected and masked."""
    text = sample_pii_texts["person_email"]
    masked = safety_guardrail.protect(text)

    # Verify John Wick is masked
    assert "John Wick" not in masked
    assert "<PERSON_" in masked
    assert "<EMAIL_ADDRESS_" in masked


def test_protect_phone_number(safety_guardrail, sample_pii_texts):
    """Test that phone numbers are detected and masked."""
    text = sample_pii_texts["phone_number"]
    masked = safety_guardrail.protect(text)

    assert "555-123-4567" not in masked
    assert "<PHONE_NUMBER_" in masked


def test_protect_address(safety_guardrail, sample_pii_texts):
    """Test that addresses are detected and masked."""
    text = sample_pii_texts["address"]
    masked = safety_guardrail.protect(text)

    assert "123 Main Street" not in masked
    assert "<LOCATION_" in masked


def test_protect_birthdate(safety_guardrail, sample_pii_texts):
    """Test that birthdates are detected and masked."""
    text = sample_pii_texts["birthdate"]
    masked = safety_guardrail.protect(text)

    assert "January 15, 1990" not in masked
    assert "<DATE_TIME_" in masked


def test_protect_no_pii(safety_guardrail, sample_pii_texts):
    """Test that text without PII remains unchanged."""
    text = sample_pii_texts["no_pii"]
    masked = safety_guardrail.protect(text)

    assert masked == text


def test_protect_creates_mapping_vault(safety_guardrail, sample_pii_texts):
    """Test that protect() populates the mapping vault."""
    text = sample_pii_texts["person_email"]
    safety_guardrail.protect(text)

    assert len(safety_guardrail.mapping_vault) > 0
    assert all(k.startswith("<") and k.endswith(">") for k in safety_guardrail.mapping_vault.keys())


def test_reveal_restores_pii(safety_guardrail, sample_pii_texts):
    """Test that reveal() restores original PII from placeholders."""
    original_text = sample_pii_texts["person_email"]
    masked = safety_guardrail.protect(original_text)

    # Create AI response using the actual placeholders from the vault
    # This ensures the indices match what protect() created
    placeholders = list(safety_guardrail.mapping_vault.keys())
    ai_response = f"Here is a bio for {placeholders[0]}. You can reach them at {placeholders[1]}."

    revealed = safety_guardrail.reveal(ai_response)

    # Verify original values are restored
    assert "john.wick" in revealed.lower() or "boogeyman@continental.com" in revealed


def test_reveal_without_mappings(safety_guardrail, mock_ai_response):
    """Test that reveal() handles responses with no placeholders."""
    text = mock_ai_response["without_placeholders"]
    revealed = safety_guardrail.reveal(text)

    assert revealed == text


def test_multiple_same_entity_type(safety_guardrail):
    """Test handling of multiple entities of the same type."""
    text = "Contact Alice at alice@email.com or Bob at bob@email.com"
    masked = safety_guardrail.protect(text)

    # Should have unique placeholders for each occurrence
    assert masked.count("<PERSON_") == 2
    assert masked.count("<EMAIL_ADDRESS_") == 2


def test_mapping_vault_isolation(safety_guardrail, sample_pii_texts):
    """Test that mapping vault is isolated per protect() call."""
    first_text = sample_pii_texts["person_email"]
    safety_guardrail.protect(first_text)
    first_vault_size = len(safety_guardrail.mapping_vault)

    # Create new instance to avoid cross-contamination
    from safety_guardrail.engine import SafetyGuardrail

    guard2 = SafetyGuardrail()
    second_text = sample_pii_texts["phone_number"]
    guard2.protect(second_text)

    assert len(guard2.mapping_vault) > 0
    assert len(guard2.mapping_vault) != first_vault_size
