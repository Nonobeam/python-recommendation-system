from fastapi import APIRouter, Query

from app.config.elasticsearch import AISearchService, elasticsearch_service
from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE
from app.model.error_code import ErrorCode
from app.model.exception_mapper import map_exception_to_error_code
from app.model.response_helper import error, success
from app.service.input_validator import InputValidator

router = APIRouter()

ai_search_service = AISearchService()


@router.get("/")
async def root():
    response_data = {"message": "Mall-Business Recommendation API", "status": "active"}
    return success(response_data)


@router.get("/health")
async def health_check():
    response_data = {"status": "healthy", "service": "recommendation-api"}
    return success(response_data)


@router.get("/ping")
async def ping():
    response_data = {"message": "pong"}
    return success(response_data)


@router.get("/search/malls", tags=["Elasticsearch Search"])
async def public_search_malls(
    q: str = Query(
        ...,
        description="Natural language search query for malls",
        example="Find premium malls with parking and elevator access",
    ),
    page: int = Query(default=1, ge=MIN_PAGE_SIZE, description="Page number for pagination (starts from 1)", example=1),
    size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description=f"Number of results to return per page ({MIN_PAGE_SIZE}-{MAX_PAGE_SIZE})",
        example=DEFAULT_PAGE_SIZE,
    ),
):
    """Public mall search using AI-powered NLP and Elasticsearch. Does not log or require authentication."""
    try:
        is_valid, error_message = InputValidator.validate_query_message(q)
        if not is_valid:
            return error(ErrorCode.VALIDATION_ERROR, error_message)

        sanitized_query = InputValidator.sanitize_message(q)
        if not sanitized_query:
            return error(ErrorCode.VALIDATION_ERROR, "Invalid query format")

        results = await elasticsearch_service.search_malls_with_ai(
            brand_id=None, query=sanitized_query, ai_service=ai_search_service, page=page, size=size
        )
        if results.get("success"):
            response_data = {
                "extracted_criteria": results["extracted_criteria"],
                "pagination": {
                    "current_page": results.get("page", page),
                    "page_size": results.get("size", size),
                    "total_results": results.get("total_found", 0),
                    "total_pages": (results.get("total_found", 0) + size - 1) // size,
                    "has_more": results.get("has_more", False),
                },
                "results": results["results"],
            }
            return success(response_data)
        else:
            error_msg = results.get("error", "Unknown error")
            if "Gemini API error: API request failed with status 503" in error_msg:
                return error(
                    ErrorCode.GEMINI_API_ERROR, "AI search service is temporarily unavailable. Please try again later."
                )
            elif "AI extraction failed" in error_msg:
                return error(
                    ErrorCode.GEMINI_API_ERROR,
                    "AI processing service is currently unavailable. Please try again later.",
                )
            else:
                return error(ErrorCode.SERVICE_UNAVAILABLE, f"Search failed: {error_msg}")
    except Exception as e:
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)
