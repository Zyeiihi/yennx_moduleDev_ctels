from fastapi import FastAPI

from app.handlers.asset_handler import router

app = FastAPI(title="Asset API", version="1.0.0")

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Asset API is running"}