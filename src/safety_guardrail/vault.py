import json
import os
import time
import uuid
from typing import Dict, Optional

try:
    import redis

    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False


class Vault:
    """Simple vault abstraction with Redis backend (if available) or in-memory fallback.

    Stores mappings for placeholders -> original values keyed by mask_id.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if REDIS_AVAILABLE:
            try:
                self.r = redis.from_url(self.redis_url)
            except Exception:
                self.r = None
        else:
            self.r = None

        # simple in-memory fallback: {mask_id: (mapping_dict, expiry_ts)}
        self._mem = {}

    def _now(self):
        return int(time.time())

    def store(self, mapping: Dict[str, str], ttl: int = 300) -> str:
        mask_id = uuid.uuid4().hex
        payload = json.dumps(mapping, ensure_ascii=False)
        if self.r:
            try:
                self.r.setex(f"vault:{mask_id}", ttl, payload)
                return mask_id
            except Exception:
                self.r = None

        # fallback
        expiry = self._now() + int(ttl)
        self._mem[mask_id] = (mapping, expiry)
        return mask_id

    def retrieve(self, mask_id: str) -> Optional[Dict[str, str]]:
        if self.r:
            try:
                val = self.r.get(f"vault:{mask_id}")
                if not val:
                    return None
                return json.loads(val)
            except Exception:
                self.r = None

        entry = self._mem.get(mask_id)
        if not entry:
            return None
        mapping, expiry = entry
        if self._now() > expiry:
            # expired
            del self._mem[mask_id]
            return None
        return mapping

    def delete(self, mask_id: str) -> None:
        if self.r:
            try:
                self.r.delete(f"vault:{mask_id}")
                return
            except Exception:
                self.r = None

        if mask_id in self._mem:
            del self._mem[mask_id]
