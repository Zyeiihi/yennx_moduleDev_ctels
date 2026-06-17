class MemoryStorage:
    """Lưu trữ dữ liệu trong RAM tuân thủ Interface Storage"""
    def __init__(self):
        self._assets = {}
        self._scan_jobs = {}

    def save_asset(self, asset) -> None:
        self._assets[asset.id] = asset

    def get_asset(self, asset_id):
        return self._assets.get(asset_id)

    def list_assets(self) -> list:
        return list(self._assets.values())

    def delete_asset(self, asset_id) -> bool:
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False

    def save_job(self, job) -> None:
        self._scan_jobs[job.id] = job

    def get_job(self, job_id):
        return self._scan_jobs.get(job_id)

    def get_jobs_by_asset(self, asset_id) -> list:
        return [job for job in self._scan_jobs.values() if job.asset_id == asset_id]

# Khởi tạo instance dùng chung cho toàn bộ ứng dụng
db = MemoryStorage()