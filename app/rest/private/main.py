from fastapi import FastAPI
from .public.public_api import router as public_router
from .business_api import router as business_router
from .mcp_api import router as mcp_router
from .search_api import router as search_router

app = FastAPI(
    title="Mall-Business Recommendation System",
    description="Comprehensive API for matching malls with businesses using AI-powered analysis",
    version="1.0.0"
)

app.include_router(public_router, prefix="/pub", tags=["Public"])
app.include_router(business_router, prefix="/pri/api/v1", tags=["Business Logic"])
app.include_router(mcp_router, prefix="/mcp", tags=["AI/MCP Integration"])
app.include_router(search_router, prefix="/pri/api/v1", tags=["Elasticsearch Search"])