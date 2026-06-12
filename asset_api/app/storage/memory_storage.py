"""
Storage layer: lưu Asset trong memory (dict), dùng threading.Lock để
đảm bảo an toàn khi nhiều request truy cập đồng thời (Bài 4).

Tương đương sync.RWMutex trong Go, ở Python ta dùng threading.Lock.
(uvicorn chạy nhiều worker/thread cho 1 process nên vẫn cần lock)
"""
import threading
from typing import Dict, List, Optional

from app.models.asset import Asset


class MemoryStorage:
    def __init__(self):
        self._data: Dict[str, Asset] = {}
        self._lock = threading.Lock()

    # Create ----------
    def create(self, asset: Asset) -> Asset:
        with self._lock:
            self._data[asset.id] = asset
        return asset

    def batch_create(self, assets: List[Asset]) -> List[Asset]:
        """Insert nhiều asset 1 lần. Gọi khi đã validate hết (all or nothing)."""
        with self._lock:
            for a in assets:
                self._data[a.id] = a
        return assets

    #Read
    def get(self, asset_id: str) -> Optional[Asset]:
        with self._lock:
            return self._data.get(asset_id)

    def list_all(self) -> List[Asset]:
        with self._lock:
            # trả về copy để bên ngoài sửa không ảnh hưởng storage
            return list(self._data.values())

    def count(self) -> int:
        with self._lock:
            return len(self._data)

    # ---------- Delete ----------
    def delete(self, asset_id: str) -> bool:
        """Trả True nếu xóa được, False nếu id không tồn tại."""
        with self._lock:
            if asset_id in self._data:
                del self._data[asset_id]
                return True
            return False

    def batch_delete(self, ids: List[str]) -> tuple[int, int]:
        """Trả về (số đã xóa, số không tìm thấy)."""
        deleted = 0
        not_found = 0
        with self._lock:
            for asset_id in ids:
                if asset_id in self._data:
                    del self._data[asset_id]
                    deleted += 1
                else:
                    not_found += 1
        return deleted, not_found


# Một instance dùng chung toàn app (singleton đơn giản)
storage = MemoryStorage()