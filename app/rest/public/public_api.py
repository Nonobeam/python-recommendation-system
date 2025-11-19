from fastapi import APIRouter, Query

from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE
from app.model.response_helper import error, success
from app.service.search_service import SearchService

router = APIRouter()
search_service = SearchService()


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
    pageNumber: int = Query(default=1, ge=1, description="Page number for pagination (starts from 1)", example=1),
    pageSize: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description=f"Number of results to return per page ({MIN_PAGE_SIZE}-{MAX_PAGE_SIZE})",
        example=DEFAULT_PAGE_SIZE,
    ),
):
    """Public booth search using AI-powered NLP and Elasticsearch. Does not log or require authentication."""
    try:
        success_flag, data, error_code, error_message = await search_service.search_booths(
            query=q, page_number=pageNumber, page_size=pageSize, brand_id=None
        )

        if success_flag:
            return success(data)
        else:
            return error(error_code, error_message)
    except Exception as e:
        from app.model.exception_mapper import map_exception_to_error_code
        from app.model.response_helper import error

        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)
