# FILE: internal/model/asset.py
import uuid
from datetime import datetime

# Scan types the system supports
SCAN_TYPES = ['dns', 'whois', 'subdomain', 'cert_trans', 'asn', 'all',
              'ip', 'port', 'ssl', 'tech', 'cve']
# Accepted asset types
ASSET_TYPES = ['domain', 'ip']


class Asset:
    """Represents a monitored asset (domain or IP address)."""
    def __init__(self, name: str, asset_type: str, tags=None, status: str = 'active'):
        if not name or not name.strip():
            raise ValueError("Asset name cannot be empty")
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Invalid asset type: {asset_type}. Must be one of {ASSET_TYPES}")
        self.id = str(uuid.uuid4())
        self.name = name.strip()
        self.type = asset_type          # 'domain' or 'ip'
        self.status = status            # 'active', 'inactive'
        self.tags = tags if tags else ["Unassigned"]
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.updated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ScanJob:
    """Represents a single scan execution job."""
    def __init__(self, asset_id: str, scan_type: str):
        if scan_type not in SCAN_TYPES:
            raise ValueError(f"Invalid scan type: {scan_type}. Must be one of {SCAN_TYPES}")
        self.id = str(uuid.uuid4())
        self.asset_id = asset_id
        self.scan_type = scan_type
        self.status = "pending"     # pending | running | completed | failed | partial
        self.started_at = None
        self.ended_at = None
        self.error = ""
        self.results = []
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "scan_type": self.scan_type,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "error": self.error,
            "results": len(self.results),
            "created_at": self.created_at,
        }
