# FILE: test/test_model.py
"""
Unit tests for internal/model/asset.py (Bài 3.1 - Model Tests)
"""
import pytest
from internal.model.asset import Asset, ScanJob, ASSET_TYPES, SCAN_TYPES


class TestAssetModel:
    """Table-driven tests for Asset model validation."""

    valid_cases = [
        ("example.com", "domain"),
        ("google.com", "domain"),
        ("127.0.0.1", "ip"),
        ("8.8.8.8", "ip"),
    ]

    invalid_cases = [
        ("", "domain", "empty name"),
        ("test.com", "invalid", "bad type"),
        ("test.com", "URL", "bad type uppercase"),
        ("test.com", "", "empty type"),
    ]

    @pytest.mark.parametrize("name,asset_type", valid_cases)
    def test_valid_asset_creation(self, name, asset_type):
        asset = Asset(name, asset_type)
        assert asset.id is not None
        assert asset.name == name
        assert asset.type == asset_type
        assert asset.status == "active"
        assert isinstance(asset.tags, list)
        assert asset.created_at.endswith("Z")

    @pytest.mark.parametrize("name,asset_type,reason", invalid_cases)
    def test_invalid_asset_raises(self, name, asset_type, reason):
        with pytest.raises((ValueError, Exception)):
            Asset(name, asset_type)

    def test_asset_to_dict_has_required_fields(self):
        asset = Asset("test.com", "domain")
        d = asset.to_dict()
        for field in ("id", "name", "type", "status", "tags", "created_at", "updated_at"):
            assert field in d, f"Missing field: {field}"

    def test_asset_default_tags(self):
        asset = Asset("test.com", "domain")
        assert asset.tags == ["Unassigned"]

    def test_asset_custom_tags(self):
        asset = Asset("test.com", "domain", tags=["Production", "Critical"])
        assert "Production" in asset.tags

    def test_asset_all_types_accepted(self):
        for t in ASSET_TYPES:
            asset = Asset("test", t)
            assert asset.type == t


class TestScanJobModel:
    """Tests for ScanJob model."""

    @pytest.mark.parametrize("scan_type", SCAN_TYPES)
    def test_valid_scan_types(self, scan_type):
        job = ScanJob("fake-asset-id", scan_type)
        assert job.scan_type == scan_type
        assert job.status == "pending"

    def test_invalid_scan_type_raises(self):
        with pytest.raises(ValueError):
            ScanJob("fake-asset-id", "hacking")

    def test_scan_job_to_dict(self):
        job = ScanJob("asset-1", "dns")
        d = job.to_dict()
        for field in ("id", "asset_id", "scan_type", "status", "created_at"):
            assert field in d

    def test_scan_job_results_count_in_dict(self):
        job = ScanJob("asset-1", "dns")
        job.results = [{"a": 1}, {"b": 2}]
        d = job.to_dict()
        assert d["results"] == 2  # count, not list
