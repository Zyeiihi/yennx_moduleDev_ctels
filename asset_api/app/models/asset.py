import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, field_validator


VALID_TYPES = {"domain", "ip", "service"}
VALID_STATUSES = {"active", "inactive"}


class Asset(BaseModel):
    """Asset lưu trong storage."""
    id: str
    name: str
    type: str
    status: str = "active"
    created_at: datetime


class AssetCreate(BaseModel):
    """Dữ liệu client gửi lên để tạo asset."""
    name: str
    type: str
    status: str = "active"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(
                f"invalid type: '{v}'. Must be one of {sorted(VALID_TYPES)}"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(
                f"invalid status: '{v}'. Must be one of {sorted(VALID_STATUSES)}"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot blank")
        return v


def new_asset(data: AssetCreate) -> Asset:
    """Tạo 1 Asset mới từ AssetCreate, tự sinh id và created_at."""
    return Asset(
        id=str(uuid.uuid4()),
        name=data.name,
        type=data.type,
        status=data.status,
        created_at=datetime.now(timezone.utc),
    )