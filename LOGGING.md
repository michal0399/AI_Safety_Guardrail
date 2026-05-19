# Test Suite Logging System

## Overview

The Safety Guardrail test suite includes a comprehensive centralized logging system that captures all test execution, PII protection validation, and LLM-as-a-Judge evaluation results.

## Architecture

### Files

1. **`logging.conf`** - Central logging configuration (log4j-style format)
2. **`tests/logger_config.py`** - Python logging initialization and helper functions
3. **`tests/pytest_logging_plugin.py`** - Pytest plugin for test session logging
4. **`logs/`** - Directory where all log files are generated

### Log Output

#### Console Output (INFO level)
- Test headers and results
- Judge evaluation summaries
- Session start/end messages

#### Log Files

- **`logs/test_suite.log`** (10 MB rotating, 5 backups)
  - Main test execution log
  - Debug-level output for debugging
  - Includes all test results and application events

- **`logs/judge_results.log`** (5 MB rotating, 3 backups)
  - LLM-as-a-Judge evaluation results only
  - Formatted for easy reading and analysis
  - Includes metric name, score, threshold, and reasoning

- **`logs/errors.log`** (5 MB rotating, 3 backups)
  - Warnings and errors only
  - Failed tests and exceptions
  - Quick reference for issues

## Configuration

### Changing Log Levels

Edit `logging.conf` to adjust log levels for each component:

```ini
# Adjust level in the logger section: DEBUG, INFO, WARNING, ERROR
[logger_deepeval_judge]
level=INFO          # ← Change this to DEBUG for verbose judge output
```

### Available Log Levels

- **DEBUG**: Verbose output, useful for troubleshooting
- **INFO**: Important information, normal test output
- **WARNING**: Warning messages and failed tests
- **ERROR**: Only error messages

### Disabling Specific Loggers

To disable a logger, remove it from the `handlers` list:

```ini
# Original (enabled):
[logger_safety_guardrail]
handlers=console_handler,file_handler

# Disabled:
[logger_safety_guardrail]
handlers=console_handler
```

## Log Output Examples

### Test Session Header
```
================================================================================
🚀 TEST SESSION STARTED
================================================================================
Time: 2026-05-17 14:23:45
Platform: 2
```

### Judge Evaluation Result
```
⚖️  Judge: PII Protection
    Status: ✅ PASS
    Score: 0.95/0.70
    Reasoning: The masked output contains no real PII values from the input.
    Only placeholders like <PERSON_0> and <EMAIL_ADDRESS_1> are used...
```

### Test Summary
```
================================================================================
📊 TEST SESSION SUMMARY
================================================================================
Total Tests:    45
✅ Passed:       41
❌ Failed:       2
⏭️  Skipped:      1
⚠️  Errors:       1
Duration:        0:00:34.234567
Exit Status:    1
================================================================================
```

### Failed Tests Section
```
❌ Failed Tests (2):
  - test_edge_cases.py::test_invalid_input
  - test_pii_leakage.py::test_address_masking
```

## Usage

### Run Tests with Logging

```bash
# Run all tests (logs to console + files)
pytest

# Run specific test category with logging
pytest -m security

# Run with verbose output
pytest -v

# Run and keep output (don't capture)
pytest -s

# Generate coverage and logs
pytest --cov=src/safety_guardrail --cov-report=html
```

### View Logs

```bash
# View main test log (last 50 lines)
tail -f logs/test_suite.log

# View judge results
cat logs/judge_results.log

# View errors
cat logs/errors.log

# Search for specific test in logs
grep "test_pii_protection" logs/test_suite.log
```

## Python API Usage

### In Test Files

```python
from logger_config import get_logger, log_judge_result

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Starting test...")
logger.warning("Potential issue detected")
logger.error("Test failed!")

# Log judge results (automatic when using fixtures, but can be manual)
log_judge_result(
    judge_logger=get_logger('deepeval_judge'),
    metric_name="PII Protection",
    score=0.95,
    reason="All PII properly masked",
    threshold=0.7
)
```

### Example: Custom Judge Test

```python
@pytest.mark.judge
def test_pii_protection_custom(safety_guardrail, pii_protection_metric):
    """Test with automatic judge result logging."""
    text = "Name: John, Email: john@example.com"
    masked = safety_guardrail.protect(text)

    test_case = LLMTestCase(
        input=text,
        actual_output=masked
    )

    # Metric automatically logs results via LoggingGEvalMetric wrapper
    pii_protection_metric.measure(test_case)
    assert pii_protection_metric.score >= pii_protection_metric.threshold
```

## Troubleshooting

### Logs Not Appearing

1. **Check directory exists**: `logs/` folder must exist
   ```bash
   mkdir -p logs
   ```

2. **Verify logging.conf path**: Should be in project root
   ```bash
   ls logging.conf
   ```

3. **Check file permissions**: Ensure write access to logs directory
   ```bash
   chmod 755 logs/
   ```

### Too Much Output

Reduce verbosity by changing log levels in `logging.conf`:
```ini
[logger_root]
level=WARNING  # Only show warnings and errors
```

### Missing Judge Results

Ensure:
1. DeepEval is installed: `pip install deepeval`
2. Test uses judge fixture: `def test_something(pii_protection_metric):`
3. `metric.measure()` is called with a test case

## Log Rotation

Log files automatically rotate when they reach size limits:
- `test_suite.log`: 10 MB, keeps 5 backups (total ~60 MB)
- `judge_results.log`: 5 MB, keeps 3 backups (total ~20 MB)
- `errors.log`: 5 MB, keeps 3 backups (total ~20 MB)

Old logs are renamed: `test_suite.log.1`, `test_suite.log.2`, etc.

## Performance Impact

Logging adds minimal overhead:
- Disk I/O is buffered
- File rotation happens in background
- Console logging is asynchronous

No performance impact on test execution time is expected.

## Future Enhancements

Potential improvements:
- HTML report generation from logs
- Real-time log viewer
- Judge score metrics dashboard
- Log search and filtering interface
- Automated alerts for failures
