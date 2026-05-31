# API Key Management & Testing Implementation Summary

This document summarizes the comprehensive API key management system, testing infrastructure, and code quality checks added to the Safety Guardrail project.

## Completed Tasks

### 1. API Key Management System ✅

#### Backend (`src/safety_guardrail/api_keys.py`)
- **Secure Key Generation**: Uses `secrets.token_urlsafe(32)` for cryptographically secure tokens
- **Hashing**: HMAC-SHA256 with app secret key (`API_KEY_SECRET`)
- **Storage**: Redis backend with in-memory fallback
- **Metadata**: Tracks owner, scopes, creation time, expiry, disabled flag
- **TTL Support**: Configurable expiration with automatic cleanup on verification

**Key Functions**:
- `generate_api_key(owner, scopes, expires_seconds)` → `(key_id, raw_token)`
- `verify_api_key(raw_token)` → `{key_id, meta}` or `None`
- `revoke_api_key(key_id)` → `bool`
- `delete_api_key(key_id)` → `bool`
- `list_api_keys()` → `[APIKeyInfo]`

#### CLI Tool (`scripts/create_api_key.py`)
Interactive command-line utility for generating API keys:
```bash
python scripts/create_api_key.py \
  --owner alice \
  --scopes protect,reveal \
  --expires-seconds 86400
```

Features:
- Clear security warnings (token shown only once)
- Owner and scope management
- Configurable TTL
- Beautiful formatted output

#### Admin Endpoints (`src/safety_guardrail/main.py`)

**Endpoint Summary**:

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/admin/api-keys` | Create new API key | ADMIN_API_KEY |
| GET | `/admin/api-keys` | List all API keys | ADMIN_API_KEY |
| POST | `/admin/api-keys/{key_id}/revoke` | Disable key | ADMIN_API_KEY |
| DELETE | `/admin/api-keys/{key_id}` | Permanently delete | ADMIN_API_KEY |

**Request/Response Models**:
- `CreateAPIKeyRequest` — owner, scopes, expires_seconds
- `CreateAPIKeyResponse` — key_id, token (raw, shown only at creation)
- `APIKeyInfo` — metadata (no raw token)
- `RevokeAPIKeyResponse` — confirmation

#### Updated Endpoints

**Protect/Reveal** now require API key authentication:
- `/api/v1/protect` — Requires `PII_SERVICE_API_KEY`
- `/api/v1/reveal` — Requires `PII_SERVICE_API_KEY`
- All require `Authorization: Bearer <token>` header

### 2. Comprehensive Test Suite ✅

#### Unit Tests (`tests/test_api_keys.py`)

**Test Classes**:
1. `TestAPIKeyGeneration` — Key generation with various parameters
2. `TestAPIKeyVerification` — Token validation and expiry
3. `TestAPIKeyRevoke` — Key revocation
4. `TestAPIKeyDelete` — Key deletion
5. `TestAPIKeyList` — Listing keys

**Coverage**:
- Basic generation
- Owner and scope assignment
- TTL/expiry handling
- Invalid/revoked/expired key detection

#### Admin Endpoint Tests

**Test Classes**:
1. `TestCreateAPIKeyEndpoint` — POST /admin/api-keys
2. `TestListAPIKeysEndpoint` — GET /admin/api-keys
3. `TestRevokeAPIKeyEndpoint` — POST .../revoke
4. `TestDeleteAPIKeyEndpoint` — DELETE /admin/api-keys/{key_id}

**Coverage**:
- Valid admin authentication
- Missing/invalid authorization (401/403)
- Happy path operations
- Error cases

#### Integration Tests

**Test Class**: `TestProtectRevealWithAPIKeys`

**Coverage**:
- Protect with valid API key
- Protect/reveal roundtrip workflow
- PII masking verification
- API key authentication enforcement
- Expired mask_id handling
- Proper restoration of original PII

**Test Markers**:
- `@pytest.mark.integration` — Full workflow tests
- `@pytest.mark.positive` — Happy path
- `@pytest.mark.negative` — Error cases
- `@pytest.mark.security` — Auth/authorization
- `@pytest.mark.api_keys` — API key specific

### 3. Pre-commit Hooks & Code Quality ✅

#### Configuration (`.pre-commit-config.yaml`)

**Hooks Configured**:
1. **black** — Code formatting (Python 3.13, 120 char lines)
2. **isort** — Import sorting (Black-compatible)
3. **pylint** — Linting (errors and fatal only)
4. **mypy** — Type checking (with Redis/requests types)
5. **bandit** — Security analysis
6. **yamllint** — YAML validation
7. **check-json, check-yaml** — Format validation
8. **detect-private-key** — Accidental secret detection
9. **end-of-file-fixer, trailing-whitespace** — Whitespace cleanup
10. **pytest** — Run API key tests before commit

#### Security Configuration (`.bandit.yml`)
- Excludes: tests, .venv
- Severity: MEDIUM and above
- Customizable skip list

#### Pytest Configuration (`pytest.ini`)

**Test Markers**:
```
unit — Unit tests
integration — Integration tests
positive — Happy path
negative — Error cases
security — Security tests
api_keys — API key tests
auth — Authentication tests
slow — Slow tests (optional)
judge — LLM-as-a-judge tests
```

**Coverage Settings**:
- Source: `src/safety_guardrail`
- Exclusions: tests, venv

### 4. Documentation ✅

#### Testing Guide (`TESTING.md`)
- Quick start commands
- Test structure overview
- Marker usage
- Running by category
- Coverage reports
- Pre-commit setup
- Writing new tests (template + best practices)
- Troubleshooting
- CI/CD integration examples

#### API Keys Documentation (`API_KEYS.md`)
- Quick start guide
- Admin endpoints with curl examples
- Configuration
- Security notes
- Python/Node.js client examples
- Storage implementation details
- Troubleshooting table

#### Updated Configuration Files

**`.env.example`**:
- API service keys (PII_SERVICE_API_KEY, ADMIN_API_KEY)
- Redis configuration (REDIS_URL)
- API key hashing secret (API_KEY_SECRET)

**`requirements.txt`**:
- Test dependencies: pytest, pytest-cov, httpx, pytest-asyncio
- Code quality: black, isort, pylint, mypy, bandit, yamllint
- Pre-commit: pre-commit

**`docker-compose.yml`**:
- Fixed duplicate service definitions
- Added environment variables for API keys
- Added health check

## Key Security Features

1. **Token Hashing**: Raw tokens never stored; only HMAC-SHA256 hashes
2. **API Key Auth**: All endpoints require Bearer token in Authorization header
3. **Admin Separation**: Separate `ADMIN_API_KEY` for key management
4. **TTL/Expiry**: Keys expire automatically; old keys cleaned up
5. **Revocation**: Keys can be disabled without deletion (audit trail)
6. **Secure Defaults**: `PII_SERVICE_API_KEY` and `ADMIN_API_KEY` required in production
7. **Pre-commit Checks**: Bandit scans for security issues before commit

## Usage Examples

### Generate an API Key

**CLI**:
```bash
python scripts/create_api_key.py --owner alice --scopes protect,reveal --expires-seconds 3600
```

**Admin Endpoint**:
```bash
curl -X POST http://localhost:8000/admin/api-keys \
  -H "Authorization: Bearer <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "bob",
    "scopes": ["protect"],
    "expires_seconds": 7200
  }'
```

### Use API Key

```bash
curl -X POST http://localhost:8000/api/v1/protect \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is alice@example.com"}'
```

### Run Tests

```bash
# All tests
pytest tests/test_api_keys.py -v

# Only unit tests
pytest tests/test_api_keys.py -m unit -v

# Integration tests
pytest tests/test_api_keys.py -m integration -v

# Security tests
pytest tests/test_api_keys.py -m security -v
```

### Run Pre-commit Checks

```bash
# Setup (one-time)
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## File Structure

```
Safety_Guardrail/
├── src/safety_guardrail/
│   ├── api_keys.py              # API key management (new)
│   ├── main.py                  # FastAPI app + admin endpoints (updated)
│   ├── vault.py                 # Mask mapping storage
│   └── ...
├── scripts/
│   ├── create_api_key.py        # CLI key generator (new)
│   └── ...
├── tests/
│   ├── test_api_keys.py         # API key tests (new)
│   ├── test_safety.py           # Safety evaluation tests
│   └── conftest.py
├── .pre-commit-config.yaml      # Pre-commit hooks (updated)
├── .bandit.yml                  # Bandit security config (new)
├── pytest.ini                   # Pytest config (updated)
├── TESTING.md                   # Testing guide (new)
├── API_KEYS.md                  # API keys documentation (new)
├── requirements.txt             # Dependencies (updated)
└── ...
```

## Testing Strategy

### Coverage by Category

- **Unit Tests** (Fast): Test individual functions (key generation, verification)
- **Integration Tests** (Slower): Test full workflows (protect → reveal)
- **Security Tests** (Auth): Verify API key enforcement
- **Negative Tests** (Edge cases): Invalid keys, expired keys, missing auth

### Test Execution

```bash
# Quick smoke test (unit only)
pytest tests/test_api_keys.py -m unit --maxfail=1

# Full test suite
pytest tests/test_api_keys.py -v --tb=short

# Coverage report
pytest tests/test_api_keys.py --cov=src/safety_guardrail --cov-report=html
```

## Environment Setup

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup pre-commit
pre-commit install

# Run tests
pytest tests/ -v

# Run formatting/linting
black src/ tests/
isort src/ tests/
```

### Docker

```bash
# Build and run with Redis
docker compose up --build

# Health check
curl http://localhost:8000/health
```

## Next Steps (Future Enhancements)

1. **Rate Limiting** — Limit requests per API key
2. **Key Rotation** — Automated key refresh policies
3. **Audit Logging** — Log all API key operations
4. **Key Scopes** — Enforce scope-based access control
5. **Metrics** — Track API usage per key
6. **Dashboard** — Web UI for key management
7. **JWKS Support** — JWT-based key exchange
8. **mTLS** — Mutual TLS for inter-service communication

## Verification Checklist

✅ API key generation and hashing
✅ Secure storage (Redis + in-memory fallback)
✅ Admin endpoints with proper auth
✅ CLI tool for key generation
✅ Protect/reveal authentication
✅ Comprehensive unit tests
✅ Integration tests (full workflows)
✅ Pre-commit hooks (code quality + tests)
✅ Security checks (bandit, type hints)
✅ Documentation (TESTING.md, API_KEYS.md)
✅ Test markers (unit, integration, security, etc.)
✅ Updated requirements.txt
✅ Fixed docker-compose.yml

## Support & Troubleshooting

For detailed troubleshooting, see:
- `TESTING.md` — Test troubleshooting
- `API_KEYS.md` — API key troubleshooting
- `CLEANUP.md` — Environment cleanup

For security concerns, see:
- `.bandit.yml` — Security rules
- `.pre-commit-config.yaml` — Code quality checks
