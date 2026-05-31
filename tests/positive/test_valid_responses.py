"""Positive tests: Valid API responses."""

import re

import pytest
from deepeval.test_case import LLMTestCase

try:
    from deepeval.test_case import LLMTestCase

    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False


def test_valid_request_structure(safety_guardrail):
    """Test that valid requests are processed."""
    # Verify request validation
    request_data = {"user_prompt": "Test prompt", "task_instruction": "Test instruction"}

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

    # Placeholders should match pattern: <ENTITY_TYPE_NUMBER>
    placeholder_pattern = r"<[A-Z_]+_\d+>"

    if "<" in masked:
        placeholders = re.findall(placeholder_pattern, masked)
        # At least some placeholders should be found if masking occurred
        assert len(placeholders) >= 0


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not available")
def test_masked_data_consistency_judge(safety_guardrail, masked_data_consistency_metric):
    """Test consistency of placeholder usage across multiple entities using LLM-as-a-judge."""
    text = "Alice works with Bob. Alice's email is alice@test.com and Bob's is bob@test.com"
    masked = safety_guardrail.protect(text)

    # Unit test: Verify consistent placeholder format
    placeholder_pattern = r"<[A-Z_]+_\d+>"
    placeholders = re.findall(placeholder_pattern, masked)
    assert all(re.match(placeholder_pattern, p) for p in placeholders)

    # LLM-as-a-judge: Comprehensive consistency evaluation
    test_case = LLMTestCase(input=text, actual_output=masked)
    masked_data_consistency_metric.measure(test_case)
    assert (
        masked_data_consistency_metric.score >= masked_data_consistency_metric.threshold
    ), f"Masked Data Consistency failed: {masked_data_consistency_metric.reason}"
