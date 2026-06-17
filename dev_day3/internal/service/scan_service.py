import threading
from datetime import datetime
from internal.storage.memory import db
from internal.service.scanners import IPScanner, PortScanner, SSLScanner, TechScanner, DummyPassiveScanners

class ScanService:
    @staticmethod
    def execute_job_worker(job_id: str):
        """Hàm chạy ngầm thu thập dữ liệu tùy theo từng loại Job"""
        job = db.get_job(job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow().isoformat() + "Z"
        
        # Tìm thông tin mục tiêu (IP hoặc tên miền) từ tài sản gốc
        asset = db.get_asset(job.asset_id)
        if not asset:
            job.status = "failed"
            job.error = "Asset isn't exist or be deleted"
            return

        target = asset.name

        try:
            # Phân phối và điều hướng đến công cụ tương ứng
            if job.scan_type == "ip":
                result = IPScanner.scan(target)
                job.results = [result]
            elif job.scan_type == "port":
                result = PortScanner.scan(target)
                job.results = [result]
            elif job.scan_type == "ssl":
                result = SSLScanner.scan(target)
                job.results = [result]
            elif job.scan_type == "tech":
                result = TechScanner.scan(target)
                job.results = [result]
            elif job.scan_type == "dns":
                job.results = [DummyPassiveScanners.scan_dns(target)]
            elif job.scan_type == "whois":
                job.results = [DummyPassiveScanners.scan_whois(target)]
            elif job.scan_type == "subdomain":
                job.results = [DummyPassiveScanners.scan_subdomain(target)]
            else:
                job.results = [{"target": target, "info": f"Passive scan type {job.scan_type} completed"}]

            job.status = "completed"
        except PermissionError as pe:
            job.status = "failed"
            job.error = str(pe)
        except Exception as e:
            job.status = "failed"
            job.error = f"Lỗi hệ thống trong quá trình quét: {str(e)}"
        finally:
            job.ended_at = datetime.utcnow().isoformat() + "Z"
            db.save_job(job)

    def start_scan(self, job) -> None:
        """Sử dụng Threading của Python để đẩy tiến trình chạy ngầm ngay lập tức"""
        db.save_job(job)
        thread = threading.Thread(target=self.execute_job_worker, args=(job.id,))
        thread.start()