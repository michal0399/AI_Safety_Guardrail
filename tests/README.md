# Test Structure for Safety Guardrail

This directory contains comprehensive tests organized by category following industry best practices for AI systems testing.

## Directory Structure

```
tests/
├── unit/                      # Unit tests for individual components
│   ├── test_engine.py        # SafetyGuardrail class unit tests
│   └── test_chat.py          # Chat module unit tests
├── integration/              # Integration tests across components
│   ├── test_safety_workflow.py   # End-to-end PII protection workflow
│   └── test_api.py          # FastAPI endpoint integration tests
├── positive/                 # Happy path / valid input tests
│   ├── test_valid_pii_masking.py  # Valid PII masking scenarios
│   └── test_valid_responses.py    # Valid API responses
├── negative/                 # Edge cases and invalid input tests
│   └── test_edge_cases.py   # Malformed input, special cases
├── regression/              # Previously fixed issues
│   └── test_known_issues.py # Tests for known issues to prevent reoccurrence
├── security/                # Security-focused tests
│   ├── test_pii_leakage.py # Ensure no PII leaks
│   └── test_prompt_injection.py # Attack vector protection
├── performance/             # Performance and efficiency tests
│   ├── test_masking_speed.py    # Latency and throughput
│   └── test_api_latency.py     # API response time
├── conftest.py             # Shared pytest fixtures
└── test_safety.py          # Legacy test file (evaluation tests)
```

## Test Categories

### 1. **Unit Tests** (`unit/`)
Tests individual components in isolation:
- SafetyGuardrail engine functions
- Masking and reveal operations
- Config loading
- Individual function behavior

**Run:** `pytest tests/unit -v`

### 2. **Integration Tests** (`integration/`)
Tests how components work together:
- Complete PII protection workflow (protect → AI → reveal)
- API endpoint integration
- Multiple PII types in single operation

**Run:** `pytest tests/integration -v`

### 3. **Positive Tests** (`positive/`)
Happy path / expected behavior:
- Valid PII detection and masking
- Various valid formats (emails, phones, dates, etc.)
- Expected API response schemas

**Run:** `pytest tests/positive -v`

### 4. **Negative Tests** (`negative/`)
Edge cases and error conditions:
- Empty inputs
- Malformed data
- Special characters and unicode
- SQL injection and XSS patterns
- Boundary conditions

**Run:** `pytest tests/negative -v`

### 5. **Regression Tests** (`regression/`)
Previously fixed issues to prevent reoccurrence:
- Birthdate masking (was missing, now fixed)
- Address masking (was missing, now fixed)
- Phone number masking (was missing, now fixed)
- Placeholder format consistency

**Run:** `pytest tests/regression -v`

### 6. **Security Tests** (`security/`)
PII protection and attack prevention:
- **PII Leakage Tests**: Ensure no sensitive data appears in masked output
  - Name masking verification
  - Email masking verification
  - Address masking verification
  - Phone masking verification
  - Complex multi-field data
  
- **Prompt Injection Tests**: Attack vector protection
  - SQL injection attempts
  - Null byte injection
  - Unicode normalization attacks
  - Role-play injection
  - Obfuscated PII bypass attempts

**Run:** `pytest tests/security -v`

### 7. **Performance Tests** (`performance/`)
Speed, efficiency, and scalability:
- Masking latency (simple and complex texts)
- Reveal operation speed
- Large text handling
- High-volume PII entity handling
- Throughput measurements
- API response times

**Run:** `pytest tests/performance -v`

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Category
```bash
pytest tests/unit -v
pytest tests/security -v
pytest tests/performance -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/safety_guardrail --cov-report=html
```

### Run Only Performance Tests
```bash
pytest tests/performance -v --tb=short
```

### Run Specific Test
```bash
pytest tests/unit/test_engine.py::test_protect_person_detection -v
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "pii_leakage" -v
```

## Test Configuration

Tests use shared fixtures defined in `conftest.py`:
- `safety_guardrail`: SafetyGuardrail instance
- `sample_pii_texts`: Dictionary of various PII text samples
- `mock_ai_response`: Mock AI responses with placeholders

## Performance Benchmarks

Expected performance targets:
- Simple text masking: < 1 second
- Complex text masking: < 5 seconds
- Reveal operation: < 0.5 seconds
- API throughput: > 10 requests/second

## Best Practices

1. **Unit tests** should test one thing only
2. **Integration tests** verify components work together
3. **Security tests** should attempt to break things intentionally
4. **Performance tests** establish baselines and catch regressions
5. **Regression tests** document known issues and their fixes

## Adding New Tests

When adding new tests:
1. Place in appropriate category directory
2. Follow naming convention: `test_<component>_<scenario>.py`
3. Use descriptive test names: `test_<what>_<expected_result>`
4. Document the purpose in docstring
5. Use fixtures from `conftest.py` where possible
6. Add to this README if creating new category
