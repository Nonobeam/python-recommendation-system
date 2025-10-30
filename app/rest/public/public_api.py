from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from app.config.elasticsearch import elasticsearch_service, AISearchService
from app.service.input_validator import InputValidator
from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE

router = APIRouter()

ai_search_service = AISearchService()

@router.get("/")
async def root():
    return {"message": "Mall-Business Recommendation API", "status": "active"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation-api"}

@router.get("/ping")
async def ping():
    return {"message": "pong"}

@router.get("/search/malls", tags=["Elasticsearch Search"])
async def public_search_malls(
    q: str = Query(
        ..., 
        description="Natural language search query for malls",
        example="Find premium malls with parking and elevator access"
    ),
    page: int = Query(
        default=1,
        ge=MIN_PAGE_SIZE,
        description="Page number for pagination (starts from 1)",
        example=1
    ),
    size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description=f"Number of results to return per page ({MIN_PAGE_SIZE}-{MAX_PAGE_SIZE})",
        example=DEFAULT_PAGE_SIZE
    )
):
    """Public mall search using AI-powered NLP and Elasticsearch. Does not log or require authentication."""
    is_valid, error_message = InputValidator.validate_query_message(q)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    sanitized_query = InputValidator.sanitize_message(q)
    if not sanitized_query:
        raise HTTPException(status_code=400, detail="Invalid query format")

    results = await elasticsearch_service.search_malls_with_ai(
        brand_id=None, query=sanitized_query, ai_service=ai_search_service, page=page, size=size
    )
    if results.get("success"):
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "extracted_criteria": results["extracted_criteria"],
                "pagination": {
                    "current_page": results.get("page", page),
                    "page_size": results.get("size", size),
                    "total_results": results.get("total_found", 0),
                    "total_pages": (results.get("total_found", 0) + size - 1) // size,
                    "has_more": results.get("has_more", False)
                },
                "results": results["results"]
            }
        )
    else:
        error_msg = results.get('error', 'Unknown error')
        raise HTTPException(status_code=503, detail=f"Search failed: {error_msg}")
