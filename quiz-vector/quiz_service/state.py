import time
import uuid
from dataclasses import dataclass

DEFAULT_TTL_SEC = 60 * 30  # 30 minutes

@dataclass
class Session:
    model: object
    created_at: float
    ttl_sec: int

class InMemoryStore:
    def __init__(self):
        self._map = {}

    def create(self, model, ttl_sec=DEFAULT_TTL_SEC) -> str:
        sid = str(uuid.uuid4())
        self._map[sid] = Session(model=model, created_at=time.time(), ttl_sec=ttl_sec)
        return sid

    def get(self, sid: str):
        s = self._map.get(sid)
        if not s:
            return None
        if time.time() - s.created_at > s.ttl_sec:
            self._map.pop(sid, None)
            return None
        return s

    def delete(self, sid: str):
        self._map.pop(sid, None)

STORE = InMemoryStore()