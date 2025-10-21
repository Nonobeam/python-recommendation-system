from fastapi import APIRouter
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Mall-Business Recommendation API", "status": "active"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation-api"}

@router.get("/ping")
async def ping():
    return {"message": "pong"}
