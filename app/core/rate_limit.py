from collections import defaultdict, deque
from threading import Lock
from time import time

from fastapi import HTTPException


class InMemoryRateLimiter:
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._blocked_until: dict[str, float] = {}
        self._used_nonces: dict[str, float] = {}
        self._lock = Lock()

    def _prune(self, bucket: deque[float], window_seconds: int, now: float):
        cutoff = now - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def ensure_allowed(self, key: str, limit: int, window_seconds: int, detail: str):
        now = time()
        with self._lock:
            blocked_until = self._blocked_until.get(key)
            if blocked_until and blocked_until > now:
                raise HTTPException(status_code=429, detail=detail)

            bucket = self._events[key]
            self._prune(bucket, window_seconds, now)
            if len(bucket) >= limit:
                raise HTTPException(status_code=429, detail=detail)

    def hit(self, key: str, limit: int, window_seconds: int, detail: str):
        now = time()
        with self._lock:
            blocked_until = self._blocked_until.get(key)
            if blocked_until and blocked_until > now:
                raise HTTPException(status_code=429, detail=detail)

            bucket = self._events[key]
            self._prune(bucket, window_seconds, now)
            if len(bucket) >= limit:
                raise HTTPException(status_code=429, detail=detail)
            bucket.append(now)

    def register_failure(self, key: str, block_seconds: int, max_attempts: int, window_seconds: int):
        now = time()
        with self._lock:
            bucket = self._events[key]
            self._prune(bucket, window_seconds, now)
            bucket.append(now)
            if len(bucket) >= max_attempts:
                self._blocked_until[key] = now + block_seconds

    def clear(self, key: str):
        with self._lock:
            self._events.pop(key, None)
            self._blocked_until.pop(key, None)

    def check_and_store_nonce(self, nonce: str, ttl_seconds: int):
        now = time()
        with self._lock:
            expired = [key for key, expires_at in self._used_nonces.items() if expires_at <= now]
            for key in expired:
                self._used_nonces.pop(key, None)
            if nonce in self._used_nonces:
                raise HTTPException(status_code=403, detail="Invalid or replayed media signature")
            self._used_nonces[nonce] = now + ttl_seconds


rate_limiter = InMemoryRateLimiter()
