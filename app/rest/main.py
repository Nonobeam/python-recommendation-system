from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.constants import SERVICE_NAME, SERVICE_VERSION
from app.exception.api_exceptions import ApplicationException
from app.middleware.jwt_middleware import JWTAuthMiddleware
from app.model.api_models import HealthCheckResponse
from app.model.error_code import ErrorCode
from app.model.exception_mapper import map_exception_to_error_code
from app.model.response_helper import error, success
from app.rest.private.recommendation_api import router as recommendation_router
from app.rest.private.search_api import router as search_router
from app.rest.public.document_api import router as document_router
from app.rest.public.public_api import router as public_router


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Mall-Business Recommendation API",
        version="1.0.0",
        description="""
            ## Mall-Business Recommendation System
            A comprehensive REST API service for matching malls with businesses based on demographics, traffic patterns,
            and budget requirements with AI-powered natural language search.
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
            {"url": "https://api.yourdomain.com", "description": "Production server"},
        ],
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication. Include the token in the Authorization header as 'Bearer <token>'",
        }
    }

    for path, path_item in openapi_schema["paths"].items():
        if path.startswith("/pri"):
            for method in path_item:
                if method in ["get", "post", "put", "delete", "patch"]:
                    path_item[method]["security"] = [{"BearerAuth": []}]

    openapi_schema["tags"] = [
        {"name": "Health Check", "description": "System health and status endpoints"},
        {"name": "Public", "description": "Public endpoints that don't require authentication"},
        {"name": "Elasticsearch Search", "description": "AI-powered search endpoints with natural language processing"},
        {"name": "Business Logic", "description": "Business recommendation and analytics endpoints"},
        {"name": "Document Intelligence", "description": "AI document processing endpoints"},
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
    contact={"name": "API Support", "email": "support@yourdomain.com"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error(ErrorCode.VALIDATION_ERROR, "Request validation failed", details=exc.errors())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = ErrorCode.INTERNAL_SERVER_ERROR
    if exc.status_code == 400:
        error_code = ErrorCode.BAD_REQUEST
    elif exc.status_code == 401:
        error_code = ErrorCode.AUTHENTICATION_ERROR
    elif exc.status_code == 403:
        error_code = ErrorCode.AUTHORIZATION_ERROR
    elif exc.status_code == 404:
        error_code = ErrorCode.NOT_FOUND
    elif exc.status_code == 503:
        error_code = ErrorCode.SERVICE_UNAVAILABLE
    return error(error_code, exc.detail or str(exc))


@app.exception_handler(ApplicationException)
async def application_exception_handler(request: Request, exc: ApplicationException):
    message = str(exc.args[0]) if exc.args else str(exc.error_code)
    return error(exc.error_code, message)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_code, message = map_exception_to_error_code(exc)
    return error(error_code, message)


@app.get("/health", response_model=HealthCheckResponse, tags=["Health Check"], summary="Service Health Check")
async def health_check():
    """
    Check the health status of the Mall-Business Recommendation API service.

    Returns basic service information including status, service name, and version.
    This endpoint is publicly accessible and doesn't require authentication.
    """
    from datetime import datetime

    response_data = {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return success(response_data)


app.include_router(public_router, prefix="/pub", tags=["Public"])
app.include_router(search_router, prefix="/pri/api/v1", tags=["Elasticsearch Search"])
app.include_router(recommendation_router, prefix="/pri/api/v1", tags=["Recommendation Engine"])
app.include_router(document_router, prefix="/pub/api/v1", tags=["Document Intelligence"])
