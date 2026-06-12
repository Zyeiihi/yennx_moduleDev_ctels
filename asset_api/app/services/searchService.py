from app.models.asset import Asset
from app.storage.memory_storage import MemoryStorage


class SearchService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def search_by_name(self, query: str) -> list[Asset]:
        if not query:
            raise ValueError("query 'q' không được để trống")

        q_lower = query.lower()
        assets = self.storage.list_all()
        matched = [a for a in assets if q_lower in a.name.lower()]
        return matched[:100]