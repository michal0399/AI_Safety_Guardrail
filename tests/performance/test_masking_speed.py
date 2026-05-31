"""Performance tests: Speed and efficiency."""

import time

import pytest


def test_masking_latency_simple(safety_guardrail):
    """Test masking latency for simple text."""
    text = "John Wick - john@example.com"

    start = time.time()
    safety_guardrail.protect(text)
    elapsed = time.time() - start

    # Should complete in under 1 second for simple text
    assert elapsed < 1.0, f"Masking took {elapsed}s (expected < 1s)"


def test_masking_latency_complex(safety_guardrail):
    """Test masking latency for complex text with multiple PII types."""
    text = (
        "John Wick, DOB: 01/15/1990, "
        "Address: 123 Main St, New York, NY 10001, "
        "Email: john@example.com, "
        "Phone: 555-1234567. "
    ) * 10  # Repeated 10 times

    start = time.time()
    safety_guardrail.protect(text)
    elapsed = time.time() - start

    # Should complete in reasonable time
    assert elapsed < 5.0, f"Masking took {elapsed}s (expected < 5s)"


def test_reveal_latency(safety_guardrail):
    """Test reveal operation latency."""
    text = "John john@example.com"
    masked = safety_guardrail.protect(text)

    start = time.time()
    safety_guardrail.reveal(masked)
    elapsed = time.time() - start

    # Reveal should be fast
    assert elapsed < 0.5, f"Reveal took {elapsed}s (expected < 0.5s)"


def test_large_text_handling(safety_guardrail):
    """Test handling of large texts."""
    # Create a large text with PII scattered throughout
    large_text = (
        "This is a large document. " * 100
        + "Contact John Wick at john@example.com for more info. "
        + "Additional content here. " * 100
    )

    start = time.time()
    masked = safety_guardrail.protect(large_text)
    elapsed = time.time() - start

    # Should handle large text reasonably
    assert elapsed < 10.0, f"Large text masking took {elapsed}s"
    assert isinstance(masked, str)


def test_many_pii_entities(safety_guardrail):
    """Test performance with many PII entities."""
    # Create text with many PII occurrences
    text_parts = []
    for i in range(50):
        text_parts.append(f"User {i}: name{i}@example.com, Phone: 555-{i:04d}")

    large_text = " ".join(text_parts)

    start = time.time()
    masked = safety_guardrail.protect(large_text)
    elapsed = time.time() - start

    # Should handle many entities
    assert elapsed < 15.0, f"Many entities masking took {elapsed}s"
    assert isinstance(masked, str)


def test_sequential_operations_latency(safety_guardrail):
    """Test latency of sequential protect/reveal operations."""
    texts = ["John john@example.com", "Jane jane@example.com", "Bob bob@example.com"]

    start = time.time()
    for text in texts:
        masked = safety_guardrail.protect(text)
        safety_guardrail.reveal(masked)
    elapsed = time.time() - start

    # Should handle multiple operations efficiently
    assert elapsed < 5.0, f"Sequential ops took {elapsed}s"


def test_mapping_vault_size_efficiency(safety_guardrail):
    """Test that mapping vault doesn't grow unexpectedly."""
    text = "Name Name Name Name Name"

    safety_guardrail.protect(text)
    vault_size = len(safety_guardrail.mapping_vault)

    # Vault should be reasonable size
    assert vault_size < 1000, f"Vault too large: {vault_size}"


@pytest.mark.parametrize("repeat_count", [1, 10, 100])
def test_throughput(safety_guardrail, repeat_count):
    """Test throughput of masking operations."""
    text = "John Wick john@example.com"

    start = time.time()
    for _ in range(repeat_count):
        safety_guardrail.protect(text)
    elapsed = time.time() - start

    throughput = repeat_count / elapsed
    # Should handle at least 10 ops per second
    assert throughput > 10, f"Low throughput: {throughput} ops/sec"
