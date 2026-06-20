# FILE: test/test_handler.py
"""
Handler (route) tests using Flask test client and mock storage (Bài 3.2 Bonus).
"""
import json
import pytest
from app import app
from internal.storage.memory import MemoryStorage
import internal.handler.router as router_module


@pytest.fixture(autouse=True)
def inject_memory_storage():
    """Swap out DB storage for in-memory storage for each test."""
    mem = MemoryStorage()
    router_module._storage = mem
    router_module._scan_service = None  # Reset so it picks up new storage
    yield mem
    router_module._storage = None
    router_module._scan_service = None


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data


class TestAssetEndpoints:

    def test_create_asset_success(self, client):
        resp = client.post("/assets",
                           data=json.dumps({"name": "test.com", "type": "domain"}),
                           content_type="application/json")
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "test.com"
        assert data["type"] == "domain"
        assert "id" in data

    def test_create_asset_missing_name(self, client):
        resp = client.post("/assets",
                           data=json.dumps({"type": "domain"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_create_asset_invalid_type(self, client):
        resp = client.post("/assets",
                           data=json.dumps({"name": "test.com", "type": "invalid"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_list_assets_empty(self, client):
        resp = client.get("/assets")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_assets_after_create(self, client):
        client.post("/assets",
                    data=json.dumps({"name": "test.com", "type": "domain"}),
                    content_type="application/json")
        resp = client.get("/assets")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    def test_delete_asset(self, client):
        create = client.post("/assets",
                             data=json.dumps({"name": "test.com", "type": "domain"}),
                             content_type="application/json")
        asset_id = create.get_json()["id"]
        del_resp = client.delete(f"/assets/{asset_id}")
        assert del_resp.status_code == 200
        # Verify it's gone
        get_resp = client.get(f"/assets/{asset_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_asset(self, client):
        resp = client.delete("/assets/does-not-exist")
        assert resp.status_code == 404


class TestScanEndpoints:

    def _create_asset(self, client, name="test.com", atype="domain"):
        resp = client.post("/assets",
                           data=json.dumps({"name": name, "type": atype}),
                           content_type="application/json")
        return resp.get_json()["id"]

    def test_start_scan_returns_202(self, client):
        asset_id = self._create_asset(client)
        resp = client.post(f"/assets/{asset_id}/scan",
                           data=json.dumps({"scan_type": "dns"}),
                           content_type="application/json")
        assert resp.status_code == 202
        data = resp.get_json()
        assert data["status"] in ("pending", "running", "completed")
        assert data["scan_type"] == "dns"

    def test_start_scan_missing_scan_type(self, client):
        asset_id = self._create_asset(client)
        resp = client.post(f"/assets/{asset_id}/scan",
                           data=json.dumps({}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_start_scan_invalid_type(self, client):
        asset_id = self._create_asset(client)
        resp = client.post(f"/assets/{asset_id}/scan",
                           data=json.dumps({"scan_type": "nmap_nuclear"}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_get_job_status(self, client):
        asset_id = self._create_asset(client)
        scan_resp = client.post(f"/assets/{asset_id}/scan",
                                data=json.dumps({"scan_type": "dns"}),
                                content_type="application/json")
        job_id = scan_resp.get_json()["id"]
        status_resp = client.get(f"/scan-jobs/{job_id}")
        assert status_resp.status_code == 200

    def test_get_job_results(self, client):
        asset_id = self._create_asset(client)
        scan_resp = client.post(f"/assets/{asset_id}/scan",
                                data=json.dumps({"scan_type": "dns"}),
                                content_type="application/json")
        job_id = scan_resp.get_json()["id"]
        results_resp = client.get(f"/scan-jobs/{job_id}/results")
        assert results_resp.status_code == 200
        data = results_resp.get_json()
        assert "results" in data
        assert "scan_type" in data

    def test_list_scans_for_asset(self, client):
        asset_id = self._create_asset(client)
        client.post(f"/assets/{asset_id}/scan",
                    data=json.dumps({"scan_type": "dns"}),
                    content_type="application/json")
        resp = client.get(f"/assets/{asset_id}/scans")
        assert resp.status_code == 200
        assert len(resp.get_json()) >= 1

    def test_cors_headers_present(self, client):
        resp = client.get("/assets")
        assert "Access-Control-Allow-Origin" in resp.headers
