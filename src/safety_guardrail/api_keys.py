import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import redis as _redis  # type: ignore
except Exception:
    _redis = None

APP_SECRET = os.getenv("API_KEY_SECRET") or os.getenv("PII_SERVICE_API_KEY") or ""
REDIS_URL = os.getenv("REDIS_URL", "")


class APIKeyStore:
    def __init__(self):
        self._redis = None
        self._in_memory: Dict[str, Dict] = {}
        if _redis:
            try:
                if REDIS_URL:
                    self._redis = _redis.from_url(REDIS_URL, decode_responses=True)
                else:
                    self._redis = _redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def _hash(self, raw: str) -> str:
        key = APP_SECRET.encode() if APP_SECRET else b""
        return hmac.new(key, raw.encode(), hashlib.sha256).hexdigest()

    def generate(
        self, owner: Optional[str] = None, scopes: Optional[List[str]] = None, expires_seconds: Optional[int] = None
    ) -> Tuple[str, str]:
        raw = secrets.token_urlsafe(32)
        key_id = str(uuid.uuid4())
        hashed = self._hash(raw)
        now = int(time.time())
        expires_at = (now + int(expires_seconds)) if expires_seconds is not None else None
        meta = {
            "key_id": key_id,
            "owner": owner,
            "scopes": scopes or [],
            "created_at": now,
            "expires_at": expires_at,
            "disabled": False,
        }
        if self._redis:
            self._redis.set(f"api_key:{key_id}", json.dumps({"hash": hashed, "meta": meta}))
            self._redis.set(f"api_key_hash:{hashed}", key_id)
            try:
                self._redis.sadd("api_keys", key_id)
            except Exception as exc:
                logger.debug("Failed to index api key %s: %s", key_id, exc)
        else:
            self._in_memory[key_id] = {"hash": hashed, "meta": meta}
        return key_id, raw

    def verify(self, raw_token: str) -> Optional[Dict]:
        hashed = self._hash(raw_token)
        now = int(time.time())
        if self._redis:
            key_id = self._redis.get(f"api_key_hash:{hashed}")
            if not key_id:
                return None
            raw = self._redis.get(f"api_key:{key_id}")
            if not raw:
                return None
            data = json.loads(raw)
            meta = data.get("meta", {})
            if meta.get("disabled"):
                return None
            expires = meta.get("expires_at")
            if expires is not None and now >= int(expires):
                return None
            return {"key_id": key_id, "meta": meta}
        else:
            for kid, rec in self._in_memory.items():
                if hmac.compare_digest(rec["hash"], hashed):
                    meta = rec["meta"]
                    if meta.get("disabled"):
                        return None
                    expires = meta.get("expires_at")
                    if expires is not None and now >= int(expires):
                        return None
                    return {"key_id": kid, "meta": meta}
            return None

    def revoke(self, key_id: str) -> bool:
        if self._redis:
            raw = self._redis.get(f"api_key:{key_id}")
            if not raw:
                return False
            data = json.loads(raw)
            data["meta"]["disabled"] = True
            self._redis.set(f"api_key:{key_id}", json.dumps(data))
            return True
        rec = self._in_memory.get(key_id)
        if not rec:
            return False
        rec["meta"]["disabled"] = True
        return True

    def delete(self, key_id: str) -> bool:
        if self._redis:
            raw = self._redis.get(f"api_key:{key_id}")
            if not raw:
                return False
            data = json.loads(raw)
            hashed = data.get("hash")
            self._redis.delete(f"api_key:{key_id}")
            if hashed:
                self._redis.delete(f"api_key_hash:{hashed}")
            try:
                self._redis.srem("api_keys", key_id)
            except Exception as exc:
                logger.debug("Failed to remove api key %s from index: %s", key_id, exc)
            return True
        return bool(self._in_memory.pop(key_id, None))

    def list(self) -> List[Dict]:
        result: List[Dict] = []
        if self._redis:
            try:
                key_ids = self._redis.smembers("api_keys") or []
            except Exception:
                key_ids = []
            for kid in key_ids:
                raw = self._redis.get(f"api_key:{kid}")
                if not raw:
                    continue
                data = json.loads(raw)
                meta = data.get("meta", {})
                result.append(meta)
        else:
            for kid, rec in self._in_memory.items():
                result.append(rec["meta"])
        return result


store = APIKeyStore()


def generate_api_key(
    owner: Optional[str] = None, scopes: Optional[List[str]] = None, expires_seconds: Optional[int] = None
) -> Tuple[str, str]:
    return store.generate(owner=owner, scopes=scopes, expires_seconds=expires_seconds)


def verify_api_key(raw_token: str) -> Optional[Dict]:
    return store.verify(raw_token)


def revoke_api_key(key_id: str) -> bool:
    return store.revoke(key_id)


def delete_api_key(key_id: str) -> bool:
    return store.delete(key_id)


def list_api_keys() -> List[Dict]:
    return store.list()
