"""
Bai 4: Concurrent-safe Create

Storage (MemoryStorage) da dung threading.Lock de bao ve _data dict
khoi race condition. Service nay chi goi xuong storage,
moi asset co id la uuid4 nen khong bao gio trung.
"""
from typing import Optional

from app.models.asset import Asset, AssetCreate, new_asset
from app.storage.memory_storage import MemoryStorage


class CreateService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def create(self, data: AssetCreate) -> Asset:
        asset = new_asset(data)
        return self.storage.create(asset)

    def get(self, asset_id: str) -> Optional[Asset]:
        return self.storage.get(asset_id)