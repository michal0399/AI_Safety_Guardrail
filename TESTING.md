# Testing Guide

This document describes the testing infrastructure, how to run tests, and best practices.

## Quick Start

### Run All Tests

```bash
pytest tests/ -v
```

### Run API Key Tests Only

```bash
pytest tests/test_api_keys.py -v
```

### Run by Marker

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Security tests
pytest -m security -v

# API key tests
pytest -m api_keys -v

# Tests excluding slow tests
pytest -m "not slow" -v
```

### Run with Coverage

```bash
pytest --cov=src/safety_guardrail --cov-report=html tests/
```

## Test Structure

Tests are organized by module and concern:

```
tests/
├── test_safety.py              # Main safety evaluation tests
├── test_api_keys.py            # API key management & protect/reveal tests
└── conftest.py                 # Shared fixtures and configuration
```

### test_api_keys.py

Comprehensive tests for API key functionality:

**Unit Tests** (mark: `@pytest.mark.unit`)
- `TestAPIKeyGeneration` — Key generation with various parameters
- `TestAPIKeyVerification` — Token verification and validation
- `TestAPIKeyRevoke` — Key revocation
- `TestAPIKeyDelete` — Key deletion
- `TestAPIKeyList` — Listing keys

**Admin Endpoint Tests** (mark: `@pytest.mark.auth`)
- `TestCreateAPIKeyEndpoint` — POST /admin/api-keys
- `TestListAPIKeysEndpoint` — GET /admin/api-keys
- `TestRevokeAPIKeyEndpoint` — POST /admin/api-keys/{key_id}/revoke
- `TestDeleteAPIKeyEndpoint` — DELETE /admin/api-keys/{key_id}

**Integration Tests** (mark: `@pytest.mark.integration`)
- `TestProtectRevealWithAPIKeys` — Full protect/reveal workflow with API key auth

## Test Markers

Available pytest markers (defined in pytest.ini):

| Marker | Purpose |
|--------|---------|
| `unit` | Unit tests for individual components |
| `integration` | Integration tests across components |
| `positive` | Happy path tests with valid inputs |
| `negative` | Edge cases and invalid input tests |
| `security` | Security-focused tests (auth, PII leakage) |
| `api_keys` | Tests for API key management |
| `auth` | Authentication/authorization tests |
| `judge` | Tests using LLM-as-a-judge |
| `slow` | Slow tests (can skip with `-m "not slow"`) |

## Running Tests

### Development (Watch Mode)

```bash
pip install pytest-watch
ptw tests/test_api_keys.py
```

### CI/CD (GitHub Actions)

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short --junitxml=junit.xml
```

### Verbose Output

```bash
pytest tests/test_api_keys.py -vv -s
```

The `-s` flag shows print statements; `-vv` shows extra verbose output.

### Debug Mode

```bash
pytest tests/test_api_keys.py -vv --pdb
```

Drops into debugger on failure.

## Pre-commit Hooks

Pre-commit hooks run automatically before commits to catch issues early.

### Setup

```bash
pip install pre-commit
pre-commit install
```

### Run Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run black --all-files
pre-commit run pytest --all-files

# Skip pre-commit for a commit
git commit --no-verify
```

### Hooks Configured

- **black** — Code formatting (Python 3.13, 120 char lines)
- **isort** — Import sorting (Black-compatible)
- **check-json, check-yaml** — JSON/YAML validation
- **bandit** — Security checks
- **pytest** — Run API key tests before commit
- **trailing-whitespace, end-of-file-fixer** — Whitespace cleanup
- **detect-private-key** — Detects accidental secrets in code

## Test Fixtures

Common fixtures defined in conftest.py and test_api_keys.py:

```python
@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def admin_key():
    """Admin API key for testing."""
    # Sets ADMIN_API_KEY env var

@pytest.fixture
def service_key():
    """Service API key for testing."""
    # Sets PII_SERVICE_API_KEY env var
```

## Writing New Tests

### Template

```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Tests for my feature."""

    @pytest.mark.positive
    def test_happy_path(self):
        """Test the happy path."""
        # Arrange
        data = {"key": "value"}

        # Act
        result = my_function(data)

        # Assert
        assert result is not None
        assert result['status'] == 'ok'

    @pytest.mark.negative
    def test_invalid_input(self):
        """Test with invalid input."""
        with pytest.raises(ValueError):
            my_function(None)
```

### Best Practices

1. **Use descriptive names** — `test_create_key_with_admin_auth` not `test_1`
2. **One assertion per test** (or related assertions) — Easier to debug failures
3. **Use fixtures** — Don't repeat setup code
4. **Mark tests** — Use `@pytest.mark.unit`, `@pytest.mark.security`, etc.
5. **Test both happy and sad paths** — Valid inputs and edge cases
6. **Docstrings** — Explain what the test verifies
7. **Arrange-Act-Assert** — Clear structure in test body

### Example: Testing an API Endpoint

```python
@pytest.mark.integration
@pytest.mark.positive
def test_create_api_key_success(client, admin_key):
    """Test creating an API key via admin endpoint."""
    # Arrange
    payload = {
        "owner": "test_user",
        "scopes": ["protect", "reveal"],
        "expires_seconds": 3600
    }
    headers = {"Authorization": f"Bearer {admin_key}"}

    # Act
    response = client.post('/admin/api-keys', json=payload, headers=headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'key_id' in data
    assert 'token' in data
    assert data['owner'] == "test_user"
```

## Troubleshooting

### Tests Fail with "Missing Authorization header"

Ensure fixtures are properly configured:
```python
def test_my_endpoint(client, admin_key):  # Fixture param required!
    pass
```

### Import Errors

Make sure tests can find the modules:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

Or use the venv:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -e .
pytest tests/
```

### Unicode/Encoding Errors on Windows

Set UTF-8 encoding:
```powershell
$env:PYTHONUTF8=1
pytest tests/
```

### Redis Connection Errors

Ensure Redis is running:
```bash
docker compose up -d redis
```

Or tests will use in-memory storage automatically.

## Coverage

Generate test coverage report:

```bash
# Terminal report
pytest --cov=src/safety_guardrail --cov-report=term-missing tests/

# HTML report (opens in browser)
pytest --cov=src/safety_guardrail --cov-report=html tests/
open htmlcov/index.html  # macOS
start htmlcov\index.html  # Windows
```

Coverage goal: **>80% for critical paths**

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/ -v --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

## Security Testing

Security-focused tests ensure API key auth and PII protection:

```bash
# Run only security tests
pytest -m security -v

# Run security + auth tests
pytest -m "security or auth" -v
```

## Performance Testing

For performance benchmarks, mark tests as `@pytest.mark.slow`:

```bash
# Skip slow tests
pytest -m "not slow" -v

# Run only slow tests
pytest -m slow -v
```

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Pre-commit hooks](https://pre-commit.com/)
