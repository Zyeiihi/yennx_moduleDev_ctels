# ĐƯỜNG DẪN FILE: internal/model/asset.py
import uuid
from datetime import datetime

# Các loại scan hệ thống hỗ trợ
SCAN_TYPES = ['dns', 'whois', 'subdomain', 'cert_trans', 'asn', 'all', 'ip', 'port', 'ssl', 'tech']
# Các loại tài sản được chấp nhận
ASSET_TYPES = ['domain', 'ip']

class Asset:
    """Định nghĩa thực thể Tài sản cần quản lý"""
    def __init__(self, name: str, asset_type: str):
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Loại asset không hợp lệ: {asset_type}")
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = asset_type # 'domain' hoặc 'ip'
        self.tags = tags if tags else ["Unassigned"]
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return self.__dict__

class ScanJob:
    """Định nghĩa một phiên quét (Job)"""
    def __init__(self, asset_id: str, scan_type: str):
        if scan_type not in SCAN_TYPES:
            raise ValueError(f"Loại scan không hợp lệ: {scan_type}")
        self.id = str(uuid.uuid4())
        self.asset_id = asset_id
        self.scan_type = scan_type
        self.status = "pending"  # pending, running, completed, failed
        self.started_at = None
        self.ended_at = None
        self.error = ""
        self.results = []
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return self.__dict__