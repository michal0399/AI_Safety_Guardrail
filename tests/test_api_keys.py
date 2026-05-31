"""
Unit and integration tests for API key management and protect/reveal endpoints.
"""

import json
import os

import pytest
from fastapi.testclient import TestClient

from safety_guardrail.api_keys import delete_api_key, generate_api_key, list_api_keys, revoke_api_key, verify_api_key
from safety_guardrail.main import app, require_admin_key, require_api_key


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def admin_key():
    """Set admin key in environment for tests."""
    admin_key = "test-admin-key-12345"
    os.environ["ADMIN_API_KEY"] = admin_key
    yield admin_key
    # Cleanup
    if "ADMIN_API_KEY" in os.environ:
        del os.environ["ADMIN_API_KEY"]


@pytest.fixture
def service_key():
    """Set service API key in environment for tests."""
    service_key = "test-service-key-12345"
    os.environ["PII_SERVICE_API_KEY"] = service_key
    yield service_key
    # Cleanup
    if "PII_SERVICE_API_KEY" in os.environ:
        del os.environ["PII_SERVICE_API_KEY"]


@pytest.mark.api_keys
class TestAPIKeyGeneration:
    """Test API key generation and storage."""

    @pytest.mark.unit
    def test_generate_api_key_basic(self):
        """Test basic API key generation."""
        key_id, token = generate_api_key()
        assert key_id is not None
        assert token is not None
        assert len(token) > 20  # Should be a reasonably long token

    @pytest.mark.unit
    def test_generate_api_key_with_owner(self):
        """Test API key generation with owner."""
        key_id, token = generate_api_key(owner="alice")
        assert key_id is not None
        assert token is not None

    @pytest.mark.unit
    def test_generate_api_key_with_scopes(self):
        """Test API key generation with scopes."""
        scopes = ["protect", "reveal"]
        key_id, token = generate_api_key(scopes=scopes)
        assert key_id is not None
        assert token is not None

    @pytest.mark.unit
    def test_generate_api_key_with_expiry(self):
        """Test API key generation with expiry."""
        key_id, token = generate_api_key(expires_seconds=3600)
        assert key_id is not None
        assert token is not None


@pytest.mark.api_keys
class TestAPIKeyVerification:
    """Test API key verification."""

    @pytest.mark.unit
    def test_verify_valid_key(self):
        """Test verification of a valid API key."""
        key_id, token = generate_api_key(owner="bob")
        result = verify_api_key(token)
        assert result is not None
        assert result["key_id"] == key_id
        assert result["meta"]["owner"] == "bob"

    @pytest.mark.unit
    def test_verify_invalid_key(self):
        """Test verification of an invalid API key."""
        result = verify_api_key("invalid-token-xyz")
        assert result is None

    @pytest.mark.unit
    def test_verify_revoked_key(self):
        """Test verification of a revoked API key."""
        key_id, token = generate_api_key()
        # Revoke it
        revoke_api_key(key_id)
        # Try to verify
        result = verify_api_key(token)
        assert result is None

    @pytest.mark.unit
    @pytest.mark.security
    def test_verify_expired_key(self):
        """Test verification of an expired API key."""
        # Generate a key that expires immediately
        key_id, token = generate_api_key(expires_seconds=0)
        import time

        time.sleep(0.1)  # Small delay
        result = verify_api_key(token)
        # Should be expired
        assert result is None


@pytest.mark.api_keys
class TestAPIKeyRevoke:
    """Test API key revocation."""

    @pytest.mark.unit
    def test_revoke_key(self):
        """Test revoking an API key."""
        key_id, token = generate_api_key()
        success = revoke_api_key(key_id)
        assert success is True
        # Verify the key is now invalid
        result = verify_api_key(token)
        assert result is None

    @pytest.mark.unit
    @pytest.mark.negative
    def test_revoke_nonexistent_key(self):
        """Test revoking a non-existent key."""
        success = revoke_api_key("nonexistent-key-id")
        assert success is False


@pytest.mark.api_keys
class TestAPIKeyDelete:
    """Test API key deletion."""

    @pytest.mark.unit
    def test_delete_key(self):
        """Test deleting an API key."""
        key_id, token = generate_api_key()
        success = delete_api_key(key_id)
        assert success is True
        # Verify the key is deleted
        result = verify_api_key(token)
        assert result is None

    @pytest.mark.unit
    @pytest.mark.negative
    def test_delete_nonexistent_key(self):
        """Test deleting a non-existent key."""
        success = delete_api_key("nonexistent-key-id")
        assert success is False


@pytest.mark.api_keys
class TestAPIKeyList:
    """Test listing API keys."""

    @pytest.mark.unit
    def test_list_keys_empty(self):
        """Test listing when no keys exist (clean slate)."""
        # Just verify it returns a list
        keys = list_api_keys()
        assert isinstance(keys, list)

    @pytest.mark.unit
    def test_list_keys_after_generation(self):
        """Test listing keys after generation."""
        initial_count = len(list_api_keys())
        key_id, token = generate_api_key(owner="charlie")
        keys = list_api_keys()
        assert len(keys) >= initial_count


@pytest.mark.auth
class TestCreateAPIKeyEndpoint:
    """Test /admin/api-keys POST endpoint."""

    @pytest.mark.integration
    @pytest.mark.positive
    def test_create_key_with_admin_auth(self, client, admin_key):
        """Test creating an API key with proper admin authorization."""
        response = client.post(
            "/admin/api-keys",
            json={"owner": "test_user", "scopes": ["protect", "reveal"], "expires_seconds": 3600},
            headers={"Authorization": f"Bearer {admin_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key_id"] is not None
        assert data["token"] is not None
        assert data["owner"] == "test_user"
        assert "protect" in data["scopes"]

    @pytest.mark.integration
    @pytest.mark.negative
    @pytest.mark.security
    def test_create_key_without_auth(self, client):
        """Test creating an API key without authorization."""
        response = client.post("/admin/api-keys", json={"owner": "test_user"})
        # Should fail (either 401 or 403)
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    @pytest.mark.negative
    @pytest.mark.security
    def test_create_key_with_invalid_auth(self, client):
        """Test creating an API key with invalid authorization."""
        response = client.post(
            "/admin/api-keys", json={"owner": "test_user"}, headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code in [401, 403]


@pytest.mark.auth
class TestListAPIKeysEndpoint:
    """Test /admin/api-keys GET endpoint."""

    @pytest.mark.integration
    @pytest.mark.positive
    def test_list_keys_with_admin_auth(self, client, admin_key):
        """Test listing API keys with proper admin authorization."""
        response = client.get("/admin/api-keys", headers={"Authorization": f"Bearer {admin_key}"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    @pytest.mark.negative
    @pytest.mark.security
    def test_list_keys_without_auth(self, client):
        """Test listing API keys without authorization."""
        response = client.get("/admin/api-keys")
        assert response.status_code in [401, 403]


@pytest.mark.auth
class TestRevokeAPIKeyEndpoint:
    """Test /admin/api-keys/{key_id}/revoke POST endpoint."""

    @pytest.mark.integration
    @pytest.mark.positive
    def test_revoke_key_with_admin_auth(self, client, admin_key):
        """Test revoking an API key with proper admin authorization."""
        # First create a key
        key_id, token = generate_api_key(owner="revoke_test")

        response = client.post(f"/admin/api-keys/{key_id}/revoke", headers={"Authorization": f"Bearer {admin_key}"})
        assert response.status_code == 200
        data = response.json()
        assert data["key_id"] == key_id

        # Verify it's revoked
        result = verify_api_key(token)
        assert result is None

    @pytest.mark.integration
    @pytest.mark.negative
    def test_revoke_nonexistent_key(self, client, admin_key):
        """Test revoking a non-existent key."""
        response = client.post("/admin/api-keys/nonexistent/revoke", headers={"Authorization": f"Bearer {admin_key}"})
        assert response.status_code == 404


@pytest.mark.auth
class TestDeleteAPIKeyEndpoint:
    """Test /admin/api-keys/{key_id} DELETE endpoint."""

    @pytest.mark.integration
    @pytest.mark.positive
    def test_delete_key_with_admin_auth(self, client, admin_key):
        """Test deleting an API key with proper admin authorization."""
        # First create a key
        key_id, token = generate_api_key(owner="delete_test")

        response = client.delete(f"/admin/api-keys/{key_id}", headers={"Authorization": f"Bearer {admin_key}"})
        assert response.status_code == 200
        data = response.json()
        assert data["key_id"] == key_id

        # Verify it's deleted
        result = verify_api_key(token)
        assert result is None


# ============ Integration Tests: Protect/Reveal with API Keys ============


@pytest.mark.integration
class TestProtectRevealWithAPIKeys:
    """Integration tests for protect/reveal endpoints with API keys."""

    @pytest.mark.positive
    def test_protect_with_valid_api_key(self, client, service_key):
        """Test protect endpoint with valid API key."""
        response = client.post(
            "/api/v1/protect",
            json={"text": "My email is alice@example.com", "ttl_seconds": 300},
            headers={"Authorization": f"Bearer {service_key}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "masked_text" in data
        assert "mask_id" in data
        assert "placeholders" in data
        # Original email should not appear in masked text
        assert "alice@example.com" not in data["masked_text"]

    @pytest.mark.negative
    @pytest.mark.security
    def test_protect_without_api_key(self, client, service_key):
        """Test protect endpoint without API key."""
        response = client.post("/api/v1/protect", json={"text": "My email is bob@example.com"})
        assert response.status_code in [401, 403]

    @pytest.mark.negative
    @pytest.mark.security
    def test_protect_with_invalid_api_key(self, client, service_key):
        """Test protect endpoint with invalid API key."""
        response = client.post(
            "/api/v1/protect",
            json={"text": "My email is charlie@example.com"},
            headers={"Authorization": "Bearer invalid-key"},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.positive
    def test_reveal_with_valid_api_key(self, client, service_key):
        """Test reveal endpoint with valid API key."""
        # First protect some text
        protect_response = client.post(
            "/api/v1/protect", json={"text": "Phone: 555-1234"}, headers={"Authorization": f"Bearer {service_key}"}
        )
        assert protect_response.status_code == 200
        protect_data = protect_response.json()
        mask_id = protect_data["mask_id"]

        # Then reveal it
        reveal_response = client.post(
            "/api/v1/reveal",
            json={"mask_id": mask_id, "masked_response": f"The user's {protect_data['masked_text']}"},
            headers={"Authorization": f"Bearer {service_key}"},
        )
        assert reveal_response.status_code == 200
        reveal_data = reveal_response.json()
        assert "restored_text" in reveal_data
        # Original phone should be restored
        assert "555-1234" in reveal_data["restored_text"]

    @pytest.mark.negative
    @pytest.mark.security
    def test_reveal_without_api_key(self, client, service_key):
        """Test reveal endpoint without API key."""
        response = client.post("/api/v1/reveal", json={"mask_id": "some-id", "masked_response": "some response"})
        assert response.status_code in [401, 403]

    @pytest.mark.positive
    def test_protect_reveal_roundtrip(self, client, service_key):
        """Test full protect-reveal roundtrip."""
        original_text = "Name: John Doe, Email: john@company.com"

        # Protect
        protect_response = client.post(
            "/api/v1/protect", json={"text": original_text}, headers={"Authorization": f"Bearer {service_key}"}
        )
        assert protect_response.status_code == 200
        protect_data = protect_response.json()
        masked_text = protect_data["masked_text"]
        mask_id = protect_data["mask_id"]

        # Masked text should not contain original PII
        assert "john@company.com" not in masked_text
        assert "John Doe" not in masked_text

        # Simulate LLM response with masked text
        llm_response = f"Processing {masked_text}"

        # Reveal
        reveal_response = client.post(
            "/api/v1/reveal",
            json={"mask_id": mask_id, "masked_response": llm_response},
            headers={"Authorization": f"Bearer {service_key}"},
        )
        assert reveal_response.status_code == 200
        reveal_data = reveal_response.json()
        restored_text = reveal_data["restored_text"]

        # Restored text should contain original PII
        assert "john@company.com" in restored_text
        assert "John Doe" in restored_text

    @pytest.mark.negative
    def test_reveal_with_expired_mask_id(self, client, service_key):
        """Test reveal with an expired mask_id."""
        response = client.post(
            "/api/v1/reveal",
            json={"mask_id": "expired-or-nonexistent-mask-id", "masked_response": "some response"},
            headers={"Authorization": f"Bearer {service_key}"},
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
