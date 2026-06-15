from typing import Optional

from app.storage.memory_storage import MemoryStorage
from app.services.common import match


class StatsService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    # 1.1 Get Assets Statistics
    def get_statistics(self) -> dict:
        assets = self.storage.list_all()

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for a in assets:
            by_type[a.type] = by_type.get(a.type, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1

        return {
            "total": len(assets),
            "by_type": by_type,
            "by_status": by_status,
        }

    # 1.2 Count Assets by Filter
    def count_by_filter(self, asset_type: Optional[str], status: Optional[str]) -> dict:
        assets = self.storage.list_all()
        filtered = [a for a in assets if match(a, asset_type, status)]

        return {
            "count": len(filtered),
            "filters": {
                "type": asset_type,
                "status": status,
            },
        }