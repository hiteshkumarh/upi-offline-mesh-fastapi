import threading
import time

class IdempotencyService:
    def __init__(self, ttl_seconds: int = 86400):
        self.seen = {}
        self.lock = threading.Lock()
        self.ttl_seconds = ttl_seconds

    def claim(self, packet_hash: str) -> bool:
        now = time.time()
        with self.lock:
            if packet_hash in self.seen:
                return False
            self.seen[packet_hash] = now
            return True

    def size(self) -> int:
        with self.lock:
            return len(self.seen)

    def evict_expired(self):
        cutoff = time.time() - self.ttl_seconds
        with self.lock:
            expired_keys = [k for k, v in self.seen.items() if v < cutoff]
            for k in expired_keys:
                del self.seen[k]

    def clear(self):
        with self.lock:
            self.seen.clear()

idempotency_service = IdempotencyService()
