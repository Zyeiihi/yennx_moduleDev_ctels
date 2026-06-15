from app.storage.memory_storage import MemoryStorage


class BatchDeleteService:
    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def batch_delete(self, ids: list[str]) -> dict:
        ids = [i.strip() for i in ids if i.strip()]
        if not ids:
            raise ValueError("ids không được rỗng")

        deleted, not_found = self.storage.batch_delete(ids)
        return {"deleted": deleted, "not_found": not_found}