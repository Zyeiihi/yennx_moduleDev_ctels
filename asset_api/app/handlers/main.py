"""
Entry point: khởi tạo FastAPI app và gắn router vào.

Chạy:
    uvicorn app.main:app --reload --port 8080
"""
from fastapi import FastAPI

from app.handlers.asset_handler import router

app = FastAPI(title="Asset API", version="1.0.0")

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Asset API is running. Xem docs tại /docs"}