# FILE: internal/storage/memory.py
"""
In-memory storage — kept for backward-compat and testing.
Production code should use DatabaseStorage from database.py.
"""


class MemoryStorage:
    """Stores data in RAM; data is lost on restart."""
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
        return [j for j in self._scan_jobs.values() if j.asset_id == asset_id]

    def get_all_results_for_asset(self, asset_id: str) -> list:
        all_results = []
        for job in self.get_jobs_by_asset(asset_id):
            for result in job.results:
                all_results.append({
                    "job_id": job.id,
                    "scan_type": job.scan_type,
                    "completed_at": job.ended_at,
                    "data": result,
                })
        return all_results
