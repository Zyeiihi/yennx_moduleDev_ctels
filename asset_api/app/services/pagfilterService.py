from typing import Optional

from app.storage.memory_storage import MemoryStorage
from app.services.common import match


class PaginationService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

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
        filtered = [a for a in assets if match(a, asset_type, status)]

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