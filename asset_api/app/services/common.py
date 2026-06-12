"""
Helper function dùng chung giữa các service.
"""
from typing import Optional
 
from app.models.asset import Asset
 
 
def match(asset: Asset, asset_type: Optional[str], status: Optional[str]) -> bool:
    """Kiểm tra asset có khớp filter type/status không."""
    if asset_type and asset.type != asset_type:
        return False
    if status and asset.status != status:
        return False
    return True
 