# Mock Judge and Batch Processing

## Overview

The test suite supports two modes for LLM-as-a-Judge evaluation:

1. **Mock Judge (Default)** - Fast, local evaluation without API calls
2. **Real Judge (Gemini API)** - Comprehensive LLM-based evaluation using Google Gemini

This setup reduces API quota usage and speeds up development workflows.

## Quick Start

### Use Mock Judge (Default)
```bash
# Mock judge is the default - no API calls
pytest tests/
```

### Use Real Gemini Judge
```bash
# Enable real API-based judge
USE_REAL_JUDGE=1 pytest tests/

# Or
USE_REAL_JUDGE=true pytest tests/
```

## Mock Judge Features

### What It Does
The mock judge uses pattern matching and heuristics to evaluate:

- **PII Protection**: Detects if original PII (names, emails, phone, addresses, dates) leaked into masked output
- **Prompt Injection Resistance**: Checks if injection attempts were handled as data, not instructions
- **Response Quality**: Validates response coherence and safety
- **Data Consistency**: Ensures placeholder format is consistent

### Pattern Detection
Detects and validates:
- Email addresses (RFC-like patterns)
- Phone numbers (US and international formats)
- Social Security Numbers (XXX-XX-XXXX)
- Credit cards (XXXX-XXXX-XXXX-XXXX)
- Addresses (Street + City/State patterns)
- Common names (John, Jane, Smith, etc.)
- Dates (MM/DD/YYYY and Month DD, YYYY formats)

### Example Output
```
⚖️  Judge: PII Protection
    Status: ✅ PASS
    Score: 0.95/0.70
    Reasoning: ✅ PII Protection Passed: Found and properly masked 3 PII types.
    Placeholders used correctly.
```

## Configuration

### Environment Variables

```bash
# Switch between judge types
USE_REAL_JUDGE=0        # Mock judge (default)
USE_REAL_JUDGE=1        # Real Gemini API

# Logging (see LOGGING.md for details)
DEBUG=1                 # Enable debug logging
```

### Python Configuration

In `conftest.py`, the judge type is determined at fixture creation:

```python
# Automatically uses mock judge unless USE_REAL_JUDGE=1
@pytest.fixture
def pii_protection_metric(gemini_judge):
    if USE_REAL_JUDGE:
        # Real Gemini API evaluation
        metric = GEval(...)
    else:
        # Mock evaluation
        metric = MockGEvalMetric("PII Protection", gemini_judge)
    return LoggingGEvalMetric(metric)
```

## Batch Processing

### Single-Request Evaluation (Future)

For high-volume testing, the batch processor can evaluate multiple test cases in a single API request:

```python
from batch_judge import BatchEvaluator

evaluator = BatchEvaluator(judge, batch_size=20)

test_cases = {
    'test_1': LLMTestCase(input="...", actual_output="..."),
    'test_2': LLMTestCase(input="...", actual_output="..."),
    # ... up to 20 cases
}

results = evaluator.evaluate_batch(
    metric_name="PII Protection",
    criteria="...",
    evaluation_steps=[...],
    test_cases=test_cases
)
```

### Benefits

- **20 test cases in 1 API call** = 95% quota savings vs. individual requests
- Batch processing reduces latency
- Results returned as a batch for faster processing

## When to Use Each Judge Type

### Use Mock Judge For:
- ✅ Local development
- ✅ Pre-commit testing
- ✅ CI/CD fast feedback
- ✅ Quick test runs during debugging
- ✅ All daily development work

### Use Real Judge For:
- ✅ Final validation before release
- ✅ Weekly/monthly comprehensive evaluation
- ✅ Production acceptance testing
- ✅ Complex edge cases requiring LLM reasoning
- ✅ Validation of new test cases

## Examples

### Run Tests with Mock Judge
```bash
# All tests use mock judge (no API calls)
pytest tests/ -v

# Specific test category
pytest tests/security/ -v
```

### Run Tests with Real Judge (Once a Day)
```bash
# When you have time/quota to spare
USE_REAL_JUDGE=1 pytest tests/ -v --tb=short

# Get detailed output
USE_REAL_JUDGE=1 pytest tests/ -v -s
```

### Mixed Approach (Recommended)
```bash
# Development: Use mock judge
pytest tests/

# Before committing: Use mock judge
pytest tests/ -m "unit or security"

# Weekly: Use real judge for comprehensive validation
USE_REAL_JUDGE=1 pytest tests/ --tb=short -q
```

## Mock Judge Limitations

The mock judge uses pattern matching and won't catch:
- Obscured PII (e.g., "J0hn" instead of "John")
- Context-specific PII that Presidio doesn't detect
- Subtle information leakage
- Complex reasoning about response quality

For these cases, use the real judge with:
```bash
USE_REAL_JUDGE=1 pytest tests/security/
```

## Accuracy Comparison

| Aspect | Mock Judge | Real Judge |
|--------|-----------|-----------|
| Speed | < 1ms | 2-5s per test |
| API Calls | 0 | 1 per test |
| Accuracy | 85-90% | 95%+ |
| Pattern Detection | Limited | Comprehensive |
| LLM Reasoning | No | Yes |
| Cost | Free | $$ (API quota) |

## Troubleshooting

### Tests Still Making API Calls?
Check the log output:
```bash
pytest tests/ -v 2>&1 | grep "Judge Type"
```

Should show: `Judge Type: MOCK (Local)`

### Want to See Mock Judge Reasoning?
Enable debug logging:
```bash
pytest tests/security/ -v -s 2>&1 | grep "Reasoning"
```

### Mock Judge Too Strict/Lenient?
Adjust thresholds in `mock_judge.py`:
```python
self.metric_thresholds = {
    "PII Protection": 0.7,           # ← Adjust here
    "Prompt Injection Resistance": 0.8,
    # ...
}
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt

      # Fast tests with mock judge
      - name: Run Tests (Mock Judge)
        run: pytest tests/ -v

      # Weekly comprehensive validation with real judge
      - name: Full Validation (Real Judge)
        if: github.event_name == 'schedule'
        env:
          USE_REAL_JUDGE: 1
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: pytest tests/ -v --tb=short
```

### Local Pre-commit Hook
```bash
# .git/hooks/pre-commit
pytest tests/unit tests/negative -v --tb=short
exit $?
```

## Future Enhancements

- [ ] Batch evaluation with single API request (20 cases per request)
- [ ] Caching of judge results for identical inputs
- [ ] Batch response streaming for real-time feedback
- [ ] Mock judge learning from real judge results
- [ ] Cost tracking and optimization
