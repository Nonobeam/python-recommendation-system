from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from rest.public.public_api import router as public_router
from rest.private.business_api import router as business_router
from rest.private.search_api import router as search_router
from middleware.jwt_middleware import JWTAuthMiddleware
from model.api_models import HealthCheckResponse
from constants import SERVICE_NAME, SERVICE_VERSION

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Mall-Business Recommendation API",
        version="1.0.0",
        description="""
## Mall-Business Recommendation System

A comprehensive REST API service for matching malls with businesses based on demographics, traffic patterns, and budget requirements with AI-powered natural language search.

### Features

- **AI-Powered Search**: Natural language processing for intelligent mall searches
- **JWT Authentication**: Secure token-based authentication for private endpoints
- **Brand Search History**: Automatic logging of all searches by brand
- **Elasticsearch Integration**: Fast, scalable search with pagination
- **Demographics Analysis**: Advanced demographic matching algorithms
- **Traffic Pattern Analysis**: Real-time visitor traffic insights

### Authentication

This API uses JWT (JSON Web Tokens) for authentication. Protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

#### Token Claims
- `sub`: User ID (required)
- `brand_id`: Brand identifier for search history tracking
- `role`: User role/permissions
- `email`: User email address

### API Structure

- **Public Endpoints** (`/pub/*`): No authentication required
- **Private Endpoints** (`/pri/*`): JWT authentication required

### Search History

All searches performed through private endpoints are automatically logged to the brand search history for analytics and audit purposes.

### Pagination

Search endpoints support pagination with the following parameters:
- `page`: Page number (starts from 1)
- `size`: Number of results per page (1-100)
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.yourdomain.com", "description": "Production server"}
        ]
    )
    
    # Add JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication. Include the token in the Authorization header as 'Bearer <token>'"
        }
    }
    
    # Add security to private endpoints
    for path, path_item in openapi_schema["paths"].items():
        if path.startswith("/pri"):
            for method in path_item:
                if method in ["get", "post", "put", "delete", "patch"]:
                    path_item[method]["security"] = [{"BearerAuth": []}]
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "Health Check",
            "description": "System health and status endpoints"
        },
        {
            "name": "Public",
            "description": "Public endpoints that don't require authentication"
        },
        {
            "name": "Elasticsearch Search", 
            "description": "AI-powered search endpoints with natural language processing"
        },
        {
            "name": "Business Logic",
            "description": "Business recommendation and analytics endpoints"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Mall-Business Recommendation API",
    description="Comprehensive API for matching malls with businesses using AI-powered analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API Support",
        "email": "support@yourdomain.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTAuthMiddleware)

@app.get("/health", response_model=HealthCheckResponse, tags=["Health Check"], summary="Service Health Check")
async def health_check():
    """
    Check the health status of the Mall-Business Recommendation API service.
    
    Returns basic service information including status, service name, and version.
    This endpoint is publicly accessible and doesn't require authentication.
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": "2025-10-21T04:00:00Z"
    }

app.include_router(public_router, prefix="/pub", tags=["Public"])
app.include_router(business_router, prefix="/pri/api/v1", tags=["Business Logic"])
app.include_router(search_router, prefix="/pri/api/v1", tags=["Elasticsearch Search"])