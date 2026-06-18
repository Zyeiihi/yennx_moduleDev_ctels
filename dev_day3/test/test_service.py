# FILE: test/test_service.py
"""
Service layer tests with mock storage (Bài 3.3 - Service Tests Bonus).
"""
import pytest
from internal.model.asset import Asset, ScanJob
from internal.storage.memory import MemoryStorage
from internal.service.scan_service import ScanService
import time


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def service(storage):
    return ScanService(storage=storage)


class TestScanService:

    def test_start_scan_creates_job(self, storage, service):
        asset = Asset("127.0.0.1", "ip")
        storage.save_asset(asset)
        job = ScanJob(asset.id, "dns")
        service.start_scan(job, storage=storage)
        # Job should be saved immediately
        saved_job = storage.get_job(job.id)
        assert saved_job is not None

    def test_scan_completes_async(self, storage, service):
        asset = Asset("127.0.0.1", "ip")
        storage.save_asset(asset)
        job = ScanJob(asset.id, "ip")
        service.start_scan(job, storage=storage)
        # Wait for background thread
        time.sleep(1.5)
        updated = storage.get_job(job.id)
        assert updated.status in ("completed", "failed", "running")

    def test_scan_fails_for_missing_asset(self, storage, service):
        job = ScanJob("nonexistent-asset-id", "dns")
        storage.save_job(job)
        service.execute_job_worker(job.id, storage=storage)
        updated = storage.get_job(job.id)
        assert updated.status == "failed"

    def test_port_scan_blocked_for_public_ip(self, storage, service):
        asset = Asset("8.8.8.8", "ip")
        storage.save_asset(asset)
        job = ScanJob(asset.id, "port")
        storage.save_job(job)  # Must save first so worker can load it
        service.execute_job_worker(job.id, storage=storage)
        updated = storage.get_job(job.id)
        # Should fail due to PermissionError
        assert updated.status == "failed"
        assert "SECURITY" in updated.error or "permission" in updated.error.lower()
