import time

from app.storage.memory_storage import MemoryStorage


class HealthService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
        self._start_time = time.time()

    def health_info(self) -> dict:
        return {
            "type": "in-memory",
            "asset_count": self.storage.count(),
        }

    def uptime_seconds(self) -> int:
        return int(time.time() - self._start_time)