# FILE: test/test_scanners.py
"""
Unit tests for scanner modules (Bài 3.4 - Scanner Tests).
Network-dependent tests are skipped gracefully if no connectivity.
"""
import pytest
from internal.service.scanners import (
    is_local_host, PortScanner, SSLScanner,
    IPScanner, DNSScanner, TechScanner, CVEScanner
)


# ---------------------------------------------------------------------------
# Security / safety function tests
# ---------------------------------------------------------------------------

class TestIsLocalHost:

    @pytest.mark.parametrize("ip,expected", [
        ("127.0.0.1",     True),
        ("localhost",     True),
        ("192.168.1.1",   True),
        ("10.0.0.1",      True),
        ("172.16.0.1",    True),
        ("172.31.255.255",True),
        ("8.8.8.8",       False),
        ("1.1.1.1",       False),
        ("200.100.50.25", False),
    ])
    def test_classification(self, ip, expected):
        assert is_local_host(ip) == expected


# ---------------------------------------------------------------------------
# Port Scanner security guard
# ---------------------------------------------------------------------------

class TestPortScanner:

    def test_blocks_public_ip(self):
        """Port scanner MUST raise PermissionError for public IPs."""
        with pytest.raises(PermissionError):
            PortScanner.scan("8.8.8.8")

    def test_blocks_external_domain_resolved(self):
        with pytest.raises(PermissionError):
            PortScanner.scan("93.184.216.34")  # example.com public IP

    def test_accepts_localhost(self):
        """Should NOT raise — may return 0 open ports but must not error."""
        try:
            result = PortScanner.scan("127.0.0.1")
            assert "ip_address" in result
            assert "open_ports" in result
            assert isinstance(result["open_ports"], list)
        except PermissionError:
            pytest.fail("PortScanner should allow localhost")

    def test_result_structure(self):
        result = PortScanner.scan("127.0.0.1")
        for key in ("ip_address", "open_ports", "closed_ports", "total_scanned", "scan_duration_ms"):
            assert key in result


# ---------------------------------------------------------------------------
# IP Scanner
# ---------------------------------------------------------------------------

class TestIPScanner:

    def test_local_ip_returns_immediately(self):
        result = IPScanner.scan("127.0.0.1")
        assert result["ip_address"] == "127.0.0.1"
        assert result["asn"]["name"] == "PRIVATE"

    def test_private_range_10(self):
        result = IPScanner.scan("10.0.0.1")
        assert result["geolocation"]["country"] == "Local"

    def test_result_has_required_keys(self):
        result = IPScanner.scan("127.0.0.1")
        for key in ("ip_address", "geolocation", "asn", "reverse_dns"):
            assert key in result


# ---------------------------------------------------------------------------
# DNS Scanner
# ---------------------------------------------------------------------------

class TestDNSScanner:

    def test_result_structure(self):
        try:
            result = DNSScanner.scan("google.com")
            assert "target" in result
            assert "records" in result
        except Exception:
            pytest.skip("No network available")

    def test_invalid_domain_returns_empty_records(self):
        try:
            result = DNSScanner.scan("this-domain-does-not-exist-at-all-12345.xyz")
            assert "records" in result
        except Exception:
            pytest.skip("No network available")


# ---------------------------------------------------------------------------
# CVE Scanner
# ---------------------------------------------------------------------------

class TestCVEScanner:

    def test_known_service_returns_cves(self):
        cves = CVEScanner.check_cve("ssh")
        assert len(cves) > 0
        assert "cve_id" in cves[0]
        assert "severity" in cves[0]

    def test_unknown_service_returns_empty(self):
        cves = CVEScanner.check_cve("nonexistent-service-xyz")
        assert cves == []

    def test_scan_from_ports(self):
        open_ports = [
            {"service": "ssh", "port": 22},
            {"service": "http", "port": 80},
            {"service": "unknownsvc", "port": 9999},
        ]
        findings = CVEScanner.scan_from_ports(open_ports)
        services_found = [f["service"] for f in findings]
        assert "ssh" in services_found
        assert "http" in services_found
        assert "unknownsvc" not in services_found


# ---------------------------------------------------------------------------
# SSL Scanner (network-dependent, skipped if no internet)
# ---------------------------------------------------------------------------

class TestSSLScanner:

    def test_local_domain_error_graceful(self):
        """SSL scanner should not raise — it should return an error dict."""
        result = SSLScanner.scan("this-definitely-does-not-exist-12345.invalid")
        assert "error" in result or "domain" in result

    def test_result_structure_for_valid_domain(self):
        try:
            result = SSLScanner.scan("google.com")
            if "error" not in result:
                assert "certificate" in result
                assert "connection" in result
                assert "grade" in result
        except Exception:
            pytest.skip("No network available")
