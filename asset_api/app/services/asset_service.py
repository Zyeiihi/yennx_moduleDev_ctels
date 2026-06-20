import time
from typing import Optional

from app.models.asset import Asset, AssetCreate, new_asset
from app.storage.memory_storage import MemoryStorage

MAX_BATCH_SIZE = 100  # Giới hạn bài 2


class AssetService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
        self._start_time = time.time()  # Phục vụ tính uptime bài 5


    def _match(self, asset: Asset, asset_type: Optional[str], status: Optional[str]) -> bool:
        """Check if an asset matches the type and status filters."""
        if asset_type and asset.type != asset_type:
            return False
        if status and asset.status != status:
            return False
        return True

    # BÀI 1: STaTISTICS APIs
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

    def count_by_filter(self, asset_type: Optional[str], status: Optional[str]) -> dict:
        assets = self.storage.list_all()
        filtered = [a for a in assets if self._match(a, asset_type, status)]

        return {
            "count": len(filtered),
            "filters": {
                "type": asset_type,
                "status": status,
            },
        }


    # BÀI 2: BATCH CREATE (All or Nothing)
    def batch_create(self, items: list[dict]) -> list[Asset]:
        if len(items) == 0:
            raise ValueError("Assets list cannot be empty")
        if len(items) > MAX_BATCH_SIZE:
            raise ValueError(f"Maximum of {MAX_BATCH_SIZE} assets allowed per request")

        # 1: Validate all items first
        validated: list[AssetCreate] = []
        for idx, item in enumerate(items):
            try:
                validated.append(AssetCreate(**item))
            except Exception as e:
                raise ValueError(f"Asset at index {idx} is invalid: {e}")

        # 2: Insert into storage only if all items are valid
        new_assets = [new_asset(v) for v in validated]
        self.storage.batch_create(new_assets)
        return new_assets

    # BÀI 3: BATCH DELETE
    def batch_delete(self, ids: list[str]) -> dict:
        ids = [i.strip() for i in ids if i.strip()]
        if not ids:
            raise ValueError("IDs list cannot be empty")

        deleted, not_found = self.storage.batch_delete(ids)
        return {"deleted": deleted, "not_found": not_found}

    # BÀI 4: CONCURRENT-SAFE CREATE & GET
    def create(self, data: AssetCreate) -> Asset:
        asset = new_asset(data)
        return self.storage.create(asset)

    def get(self, asset_id: str) -> Optional[Asset]:
        return self.storage.get(asset_id)

    # BÀI 5: IN-MEMORY HEALTH CHECK
    def health_info(self) -> dict:
        return {
            "type": "in-memory",
            "asset_count": self.storage.count(),
        }

    def uptime_seconds(self) -> int:
        return int(time.time() - self._start_time)

    # BÀI 6: PAGINATION & FILTERING (BONUS)
    def list_assets(
        self,
        page: int,
        limit: int,
        asset_type: Optional[str],
        status: Optional[str],
    ) -> dict:
        if page < 1:
            page = 1
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100

        assets = self.storage.list_all()
        filtered = [a for a in assets if self._match(a, asset_type, status)]

        total = len(filtered)
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        start = (page - 1) * limit
        end = start + limit
        page_items = filtered[start:end]

        return {
            "data": page_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            },
        }

    # BÀI 7: SEARCH BY NAME (BONUS)
    def search_by_name(self, query: str) -> list[Asset]:
        if not query:
            raise ValueError("query 'q' cannot empty")

        q_lower = query.lower()
        assets = self.storage.list_all()
        matched = [a for a in assets if q_lower in a.name.lower()]
        return matched[:100]