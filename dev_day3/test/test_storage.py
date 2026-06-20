# FILE: test/test_storage.py
"""
Tests for MemoryStorage (used as baseline; DatabaseStorage uses same interface).
"""
import pytest
from internal.model.asset import Asset, ScanJob
from internal.storage.memory import MemoryStorage


@pytest.fixture
def storage():
    return MemoryStorage()


class TestMemoryStorage:

    def test_save_and_get_asset(self, storage):
        asset = Asset("test.com", "domain")
        storage.save_asset(asset)
        retrieved = storage.get_asset(asset.id)
        assert retrieved is not None
        assert retrieved.name == "test.com"

    def test_list_assets_empty(self, storage):
        assert storage.list_assets() == []

    def test_list_assets(self, storage):
        storage.save_asset(Asset("a.com", "domain"))
        storage.save_asset(Asset("b.com", "domain"))
        assert len(storage.list_assets()) == 2

    def test_delete_asset(self, storage):
        asset = Asset("delete-me.com", "domain")
        storage.save_asset(asset)
        result = storage.delete_asset(asset.id)
        assert result is True
        assert storage.get_asset(asset.id) is None

    def test_delete_nonexistent_asset(self, storage):
        assert storage.delete_asset("nonexistent-id") is False

    def test_save_and_get_job(self, storage):
        asset = Asset("test.com", "domain")
        storage.save_asset(asset)
        job = ScanJob(asset.id, "dns")
        storage.save_job(job)
        retrieved = storage.get_job(job.id)
        assert retrieved is not None
        assert retrieved.scan_type == "dns"

    def test_get_jobs_by_asset(self, storage):
        asset = Asset("test.com", "domain")
        storage.save_asset(asset)
        j1 = ScanJob(asset.id, "dns")
        j2 = ScanJob(asset.id, "ssl")
        storage.save_job(j1)
        storage.save_job(j2)
        jobs = storage.get_jobs_by_asset(asset.id)
        assert len(jobs) == 2

    def test_get_all_results_for_asset(self, storage):
        asset = Asset("test.com", "domain")
        storage.save_asset(asset)
        job = ScanJob(asset.id, "dns")
        from datetime import datetime
        job.status = "completed"
        job.results = [{"records": {"A": ["1.1.1.1"]}}]
        job.ended_at = datetime.utcnow().isoformat() + "Z"
        storage.save_job(job)
        results = storage.get_all_results_for_asset(asset.id)
        assert len(results) == 1
        assert results[0]["scan_type"] == "dns"
