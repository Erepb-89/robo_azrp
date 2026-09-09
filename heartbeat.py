import time
import threading


class Heartbeat:
    def __init__(self, names, ttl_sec=10.0):
        self.ttl = ttl_sec
        self._ts = {name: 0.0 for name in names}
        self._lock = threading.Lock()

    def beat(self, name: str):
        now = time.monotonic()
        with self._lock:
            self._ts[name] = now

    def state(self):
        now = time.monotonic()
        with self._lock:
            return {name: (now - ts <= self.ttl) for name, ts in self._ts.items()}
