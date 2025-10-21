from fastapi import FastAPI
import sys
from pathlib import Path

# Add the app directory to the path
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from rest.public.public_api import router as public_router
from rest.private.business_api import router as business_router
from rest.private.search_api import router as search_router

app = FastAPI(
    title="Mall-Business Recommendation System",
    description="Comprehensive API for matching malls with businesses using AI-powered analysis",
    version="1.0.0"
)

app.include_router(public_router, prefix="/pub", tags=["Public"])
app.include_router(business_router, prefix="/pri/api/v1", tags=["Business Logic"])
app.include_router(search_router, prefix="/pri/api/v1", tags=["Elasticsearch Search"])