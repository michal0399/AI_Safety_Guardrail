import os
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from safety_guardrail.api_keys import delete_api_key, generate_api_key, list_api_keys, revoke_api_key, verify_api_key
from safety_guardrail.chat import safe_chat
from safety_guardrail.engine_enhanced import EnhancedSafetyGuardrail
from safety_guardrail.vault import Vault

app = FastAPI(
    title="AI Safety Guardrail Proxy", description="An API that sanitizes PII locally before routing prompts to an LLM."
)


def require_api_key(authorization: Optional[str] = Header(None)):
    api_key = os.getenv("PII_SERVICE_API_KEY", "")
    if not api_key:
        return True  # disabled if no key configured
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


def require_admin_key(authorization: Optional[str] = Header(None)):
    """Check admin authorization header for admin endpoints."""
    admin_api_key = os.getenv("ADMIN_API_KEY", "")
    if not admin_api_key:
        raise HTTPException(status_code=403, detail="Admin endpoints not configured")
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


class ChatRequest(BaseModel):
    user_prompt: str
    task_instruction: str = "You are a helpful assistant."


# Expanded response schema for transparency
class ChatResponse(BaseModel):
    masked_prompt: str
    ai_raw_response: str
    final_output: str


class ProtectRequest(BaseModel):
    text: str
    language: Optional[str] = None
    ttl_seconds: Optional[int] = 300


class ProtectResponse(BaseModel):
    masked_text: str
    mask_id: str
    placeholders: dict


class RevealRequest(BaseModel):
    mask_id: str
    masked_response: str
    delete_after_reveal: Optional[bool] = True


class RevealResponse(BaseModel):
    restored_text: str


class CreateAPIKeyRequest(BaseModel):
    owner: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_seconds: Optional[int] = 300


class CreateAPIKeyResponse(BaseModel):
    key_id: str
    token: str
    owner: Optional[str] = None
    scopes: List[str] = []
    expires_seconds: int


class APIKeyInfo(BaseModel):
    key_id: str
    owner: Optional[str] = None
    scopes: List[str] = []
    created_at: int
    expires_at: Optional[int] = None
    disabled: bool


class RevokeAPIKeyResponse(BaseModel):
    message: str
    key_id: str


# singletons
guard = EnhancedSafetyGuardrail()
vault = Vault()


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker container."""
    return {"status": "healthy", "service": "Safety Guardrail AI Proxy"}


@app.post("/api/v1/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def handle_chat(payload: ChatRequest):
    try:
        # This now returns a dictionary matching the ChatResponse schema
        result_data = safe_chat(user_prompt=payload.user_prompt, task_instruction=payload.task_instruction)
        return ChatResponse(**result_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/api/v1/protect", response_model=ProtectResponse, dependencies=[Depends(require_api_key)])
async def protect(req: ProtectRequest):
    try:
        masked = guard.protect(req.text, language=req.language)
        # capture mapping and store in vault
        mapping = dict(guard.mapping_vault)
        mask_id = vault.store(mapping, ttl=req.ttl_seconds or 300)
        # clear internal guard vault to avoid memory buildup
        guard.clear_vault()
        return ProtectResponse(masked_text=masked, mask_id=mask_id, placeholders=mapping)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reveal", response_model=RevealResponse, dependencies=[Depends(require_api_key)])
async def reveal(req: RevealRequest):
    mapping = vault.retrieve(req.mask_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="mask_id not found or expired")
    # perform replacements
    restored = req.masked_response
    for placeholder, original in mapping.items():
        restored = restored.replace(placeholder, original)
    if req.delete_after_reveal:
        vault.delete(req.mask_id)
    return RevealResponse(restored_text=restored)


# ============ Admin Endpoints (API Key Management) ============


@app.post("/admin/api-keys", response_model=CreateAPIKeyResponse, dependencies=[Depends(require_admin_key)])
async def create_api_key(req: CreateAPIKeyRequest):
    """Create a new API key (admin only). Returns the raw token (shown only once)."""
    try:
        key_id, raw_token = generate_api_key(
            owner=req.owner, scopes=req.scopes, expires_seconds=req.expires_seconds or 300
        )
        return CreateAPIKeyResponse(
            key_id=key_id,
            token=raw_token,
            owner=req.owner,
            scopes=req.scopes or [],
            expires_seconds=req.expires_seconds or 300,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/api-keys", response_model=List[APIKeyInfo], dependencies=[Depends(require_admin_key)])
async def list_all_api_keys():
    """List all API keys (admin only). Does not include raw tokens."""
    try:
        all_keys = list_api_keys()
        return [
            APIKeyInfo(
                key_id=k.get("key_id"),
                owner=k.get("owner"),
                scopes=k.get("scopes", []),
                created_at=k.get("created_at"),
                expires_at=k.get("expires_at"),
                disabled=k.get("disabled", False),
            )
            for k in all_keys
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/admin/api-keys/{key_id}/revoke", response_model=RevokeAPIKeyResponse, dependencies=[Depends(require_admin_key)]
)
async def revoke_key(key_id: str):
    """Revoke an API key by marking it disabled (admin only)."""
    try:
        success = revoke_api_key(key_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Key ID {key_id} not found")
        return RevokeAPIKeyResponse(message="Key revoked successfully", key_id=key_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/api-keys/{key_id}", dependencies=[Depends(require_admin_key)])
async def delete_key(key_id: str):
    """Delete an API key permanently (admin only)."""
    try:
        success = delete_api_key(key_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Key ID {key_id} not found")
        return {"message": "Key deleted successfully", "key_id": key_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
