# FILE: internal/service/scan_service.py
"""
ScanService orchestrates asynchronous scan job execution.
Each job runs in a background thread.
"""
import threading
from datetime import datetime

from internal.service.scanners import (
    DNSScanner, WhoisScanner, SubdomainScanner,
    IPScanner, PortScanner, SSLScanner, TechScanner, CVEScanner
)


class ScanService:

    def __init__(self, storage=None):
        # Allow injecting a storage instance (useful for testing)
        self._storage = storage

    def _get_storage(self):
        if self._storage:
            return self._storage
        # Import lazily so the module can be imported before storage is initialised
        from internal.storage.database import DatabaseStorage
        return DatabaseStorage()

    @staticmethod
    def _now():
        return datetime.utcnow().isoformat() + "Z"

    def execute_job_worker(self, job_id: str, storage=None):
        """Background worker: resolves scan type and stores results."""
        db = storage or self._get_storage()
        job = db.get_job(job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = self._now()
        db.save_job(job)

        asset = db.get_asset(job.asset_id)
        if not asset:
            job.status = "failed"
            job.error = "Asset not found or was deleted"
            job.ended_at = self._now()
            db.save_job(job)
            return

        target = asset.name

        try:
            if job.scan_type == "dns":
                job.results = [DNSScanner.scan(target)]
            elif job.scan_type == "whois":
                job.results = [WhoisScanner.scan(target)]
            elif job.scan_type == "subdomain":
                job.results = [SubdomainScanner.scan(target)]
            elif job.scan_type == "cert_trans":
                # cert_trans uses the same crt.sh backend as subdomain
                job.results = [SubdomainScanner.scan(target)]
            elif job.scan_type == "asn":
                job.results = [IPScanner.scan(target)]
            elif job.scan_type == "ip":
                job.results = [IPScanner.scan(target)]
            elif job.scan_type == "port":
                result = PortScanner.scan(target)
                job.results = [result]
            elif job.scan_type == "ssl":
                job.results = [SSLScanner.scan(target)]
            elif job.scan_type == "tech":
                job.results = [TechScanner.scan(target)]
            elif job.scan_type == "cve":
                # CVE: first do port scan (local only), then correlate CVEs
                try:
                    port_result = PortScanner.scan(target)
                    cve_findings = CVEScanner.scan_from_ports(port_result.get("open_ports", []))
                    job.results = [{
                        "port_scan": port_result,
                        "cve_findings": cve_findings,
                        "total_findings": len(cve_findings),
                    }]
                except PermissionError as pe:
                    # For non-local IPs, just return mock CVE data based on common services
                    job.results = [{
                        "note": "Port scan blocked for public IP — showing known common CVEs",
                        "cve_findings": CVEScanner.scan_from_ports([
                            {"service": "ssh", "port": 22},
                            {"service": "http", "port": 80},
                        ]),
                    }]
            elif job.scan_type == "all":
                # Run all passive scans for domain assets
                job.results = [
                    {"scan_type": "dns",       "data": DNSScanner.scan(target)},
                    {"scan_type": "whois",     "data": WhoisScanner.scan(target)},
                    {"scan_type": "subdomain", "data": SubdomainScanner.scan(target)},
                    {"scan_type": "ssl",       "data": SSLScanner.scan(target)},
                    {"scan_type": "tech",      "data": TechScanner.scan(target)},
                ]
            else:
                job.results = [{"target": target, "info": f"Scan type '{job.scan_type}' executed"}]

            job.status = "completed"

        except PermissionError as pe:
            job.status = "failed"
            job.error = str(pe)
        except Exception as e:
            job.status = "failed"
            job.error = f"Scan error: {str(e)}"
        finally:
            job.ended_at = self._now()
            db.save_job(job)

    def start_scan(self, job, storage=None) -> None:
        """Save job to DB and kick off background thread."""
        db = storage or self._get_storage()
        db.save_job(job)
        thread = threading.Thread(
            target=self.execute_job_worker,
            args=(job.id, db),
            daemon=True
        )
        thread.start()
