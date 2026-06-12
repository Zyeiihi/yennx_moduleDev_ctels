"""
AssetService: facade gom tat ca service con (1 file/bai) lai thanh 1
object duy nhat, de handler chi can goi service.xxx() nhu cu.

Moi bai tap nam o 1 file rieng trong app/services/:
- stats_service.py          -> Bai 1
- batch_create_service.py    -> Bai 2
- batch_delete_service.py    -> Bai 3
- create_service.py          -> Bai 4
- health_service.py          -> Bai 5
- pagination_service.py      -> Bai 6 (bonus)
- search_service.py          -> Bai 7 (bonus)
"""
from app.storage.memory_storage import MemoryStorage

from app.services.stats_service import StatsService
from app.services.batch_create_service import BatchCreateService
from app.services.batch_delete_service import BatchDeleteService
from app.services.create_service import CreateService
from app.services.health_service import HealthService
from app.services.pagination_service import PaginationService
from app.services.search_service import SearchService


class AssetService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

        self._stats = StatsService(storage)
        self._batch_create = BatchCreateService(storage)
        self._batch_delete = BatchDeleteService(storage)
        self._create = CreateService(storage)
        self._health = HealthService(storage)
        self._pagination = PaginationService(storage)
        self._search = SearchService(storage)

    # ---- Bai 1 ----
    def get_statistics(self):
        return self._stats.get_statistics()

    def count_by_filter(self, asset_type, status):
        return self._stats.count_by_filter(asset_type, status)

    # ---- Bai 2 ----
    def batch_create(self, items):
        return self._batch_create.batch_create(items)

    # ---- Bai 3 ----
    def batch_delete(self, ids):
        return self._batch_delete.batch_delete(ids)

    # ---- Bai 4 ----
    def create(self, data):
        return self._create.create(data)

    def get(self, asset_id):
        return self._create.get(asset_id)

    # ---- Bai 5 ----
    def health_info(self):
        return self._health.health_info()

    def uptime_seconds(self):
        return self._health.uptime_seconds()

    # ---- Bai 6 ----
    def list_assets(self, page, limit, asset_type, status):
        return self._pagination.list_assets(page, limit, asset_type, status)

    # ---- Bai 7 ----
    def search_by_name(self, query):
        return self._search.search_by_name(query)