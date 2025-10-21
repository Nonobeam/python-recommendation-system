from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from rest.public.public_api import router as public_router
from rest.private.business_api import router as business_router
from rest.private.search_api import router as search_router
from middleware.jwt_middleware import JWTAuthMiddleware

app = FastAPI(
    title="Mall-Business Recommendation System",
    description="Comprehensive API for matching malls with businesses using AI-powered analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTAuthMiddleware)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "mall-recommendation-system",
        "version": "1.0.0"
    }

app.include_router(public_router, prefix="/pub", tags=["Public"])
app.include_router(business_router, prefix="/pri/api/v1", tags=["Business Logic"])
app.include_router(search_router, prefix="/pri/api/v1", tags=["Elasticsearch Search"])