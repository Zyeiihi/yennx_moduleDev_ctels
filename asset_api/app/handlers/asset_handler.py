from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.asset import AssetCreate
from app.services.asset_service import AssetService
from app.storage.memory_storage import storage

router = APIRouter()
service = AssetService(storage)


class BatchCreateRequest(BaseModel):
    assets: list[dict]


#Bài 1: Statistics APIs ============

@router.get("/assets/stats")
def get_stats():
    return service.get_statistics()


@router.get("/assets/count")
def count_assets(
    type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    return service.count_by_filter(type, status)


#Bài 2: Batch Create ============

@router.post("/assets/batch", status_code=201)
def batch_create_assets(req: BatchCreateRequest):
    try:
        created = service.batch_create(req.assets)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "created": len(created),
        "ids": [a.id for a in created],
    }


#Bài 3: Batch Delete ============

@router.delete("/assets/batch")
def batch_delete_assets(ids: str = Query(..., description="comma-separated ids")):
    id_list = ids.split(",")
    try:
        result = service.batch_delete(id_list)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


#Bài 4: Create 1 asset (dùng để test concurrent) ============

@router.post("/assets", status_code=201)
def create_asset(data: AssetCreate):
    asset = service.create(data)
    return asset


#Bài 5: Health Check ============

@router.get("/health")
def health_check():
    import datetime

    return {
        "status": "ok",
        "storage": service.health_info(),
        "uptime_seconds": service.uptime_seconds(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


#Bài 6: Pagination & Filtering ============

@router.get("/assets")
def list_assets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    return service.list_assets(page, limit, type, status)


# Bài 7: Search by Name ============

@router.get("/assets/search")
def search_assets(q: str = Query(...)):
    try:
        results = service.search_by_name(q)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return results



@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    asset = service.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset