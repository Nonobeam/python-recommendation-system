from fastapi import APIRouter

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
