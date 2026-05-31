# API Key Management

This document describes how to generate, manage, and use API keys for the Safety Guardrail service.

## Quick Start

### 1. Generate an API Key (CLI)

```bash
python scripts/create_api_key.py --owner alice --scopes protect,reveal --expires-seconds 86400
```

Output:
```
================================================================================
✓ API Key generated successfully!
================================================================================
Key ID:    9a2e28b3-23e2-4127-8181-9e344027528d
Token:     m_OUTj4n0m7tXlxmR_UNpnbRWshlc08CcnTvkMh2mg0
Owner:     alice
Scopes:    protect, reveal
Expires:   86400s from now
================================================================================

⚠️  IMPORTANT:
  - This is the ONLY time the raw token will be displayed.
  - Store it in a secure location (e.g., password manager, .env file).
  - Do NOT commit tokens to version control.
  - Use as Authorization header: Bearer <token>
```

### 2. Use the API Key

Add the token to your request headers:

```bash
curl -X POST http://localhost:8000/api/v1/protect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer m_OUTj4n0m7tXlxmR_UNpnbRWshlc08CcnTvkMh2mg0" \
  -d '{"text": "My email is alice@example.com"}'
```

## Admin Endpoints

Admin endpoints require the `ADMIN_API_KEY` environment variable to be set and the `Authorization: Bearer <ADMIN_API_KEY>` header.

### Create an API Key

```http
POST /admin/api-keys
Authorization: Bearer <ADMIN_API_KEY>
Content-Type: application/json

{
  "owner": "alice",
  "scopes": ["protect", "reveal"],
  "expires_seconds": 86400
}
```

Response:
```json
{
  "key_id": "9a2e28b3-23e2-4127-8181-9e344027528d",
  "token": "m_OUTj4n0m7tXlxmR_UNpnbRWshlc08CcnTvkMh2mg0",
  "owner": "alice",
  "scopes": ["protect", "reveal"],
  "expires_seconds": 86400
}
```

### List All API Keys

```http
GET /admin/api-keys
Authorization: Bearer <ADMIN_API_KEY>
```

Response:
```json
[
  {
    "key_id": "9a2e28b3-23e2-4127-8181-9e344027528d",
    "owner": "alice",
    "scopes": ["protect", "reveal"],
    "created_at": 1719794400,
    "expires_at": 1719880800,
    "disabled": false
  }
]
```

### Revoke an API Key

Disables a key without deleting it (keeps audit trail):

```http
POST /admin/api-keys/{key_id}/revoke
Authorization: Bearer <ADMIN_API_KEY>
```

Response:
```json
{
  "message": "Key revoked successfully",
  "key_id": "9a2e28b3-23e2-4127-8181-9e344027528d"
}
```

### Delete an API Key

Permanently removes a key:

```http
DELETE /admin/api-keys/{key_id}
Authorization: Bearer <ADMIN_API_KEY>
```

Response:
```json
{
  "message": "Key deleted successfully",
  "key_id": "9a2e28b3-23e2-4127-8181-9e344027528d"
}
```

## Configuration

Set environment variables in `.env` or pass them to the FastAPI service:

```bash
export PII_SERVICE_API_KEY=your-service-key
export ADMIN_API_KEY=your-admin-key
export REDIS_URL=redis://localhost:6379/0
export API_KEY_SECRET=your-hashing-secret

# Start the service
uvicorn src.safety_guardrail.main:app --reload
```

## Security Notes

- **Never log or print raw tokens** after generation.
- **Store tokens securely**: password manager, encrypted `.env`, secrets vault.
- **Rotate regularly**: Set short TTLs (expires_seconds) and regenerate periodically.
- **Use separate admin key**: Keep `ADMIN_API_KEY` separate from `PII_SERVICE_API_KEY`.
- **HTTPS only**: Always use HTTPS in production.
- **Scope limitation**: Use scopes to restrict what each key can do (reserved for future use).

## Storage

Keys are stored in Redis (or in-memory fallback) with:
- **Hashed tokens**: Only HMAC-SHA256 hashes are stored, not raw tokens.
- **Metadata**: key_id, owner, scopes, created_at, expires_at, disabled flag.
- **TTL**: Expired keys are automatically filtered during verification.

## Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "m_OUTj4n0m7tXlxmR_UNpnbRWshlc08CcnTvkMh2mg0"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Protect text
response = requests.post(
    f"{BASE_URL}/api/v1/protect",
    json={"text": "My phone is 555-1234"},
    headers=headers
)
print(response.json())
```

### Node.js Client

```javascript
const BASE_URL = "http://localhost:8000";
const API_KEY = "m_OUTj4n0m7tXlxmR_UNpnbRWshlc08CcnTvkMh2mg0";

const headers = {
  "Authorization": `Bearer ${API_KEY}`,
  "Content-Type": "application/json"
};

fetch(`${BASE_URL}/api/v1/protect`, {
  method: "POST",
  headers,
  body: JSON.stringify({ text: "My email is alice@example.com" })
}).then(r => r.json()).then(console.log);
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `401 Missing Authorization header` | Add `Authorization: Bearer <token>` to request |
| `403 Invalid API key` | Check that your token is correct and not expired |
| `404 mask_id not found or expired` | The mask_id has expired (default 300s); create a new one |
| `403 Admin endpoints not configured` | Set `ADMIN_API_KEY` env var to enable admin endpoints |
| Keys stored in-memory, not Redis | Check `REDIS_URL` env var; Redis connection may have failed |
