from app.models.asset import Asset, AssetCreate, new_asset
from app.storage.memory_storage import MemoryStorage

MAX_BATCH_SIZE = 100  # limit toi da 100 assets/request


class BatchCreateService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def batch_create(self, items: list[dict]) -> list[Asset]:
        """
        Validate toan bo truoc (all or nothing).
        Neu co 1 item loi -> raise ValueError ngay, KHONG tao gi ca.
        """
        if len(items) == 0:
            raise ValueError("assets không được rỗng")
        if len(items) > MAX_BATCH_SIZE:
            raise ValueError(f"Tối đa {MAX_BATCH_SIZE} assets mỗi request")

        # Buoc 1: validate het, chua insert gi
        validated: list[AssetCreate] = []
        for idx, item in enumerate(items):
            try:
                validated.append(AssetCreate(**item))
            except Exception as e:
                raise ValueError(f"Asset thứ {idx} không hợp lệ: {e}")

        # Buoc 2: chi khi tat ca OK moi tao Asset object + insert
        new_assets = [new_asset(v) for v in validated]
        self.storage.batch_create(new_assets)
        return new_assets