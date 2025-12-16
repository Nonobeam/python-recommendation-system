from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from app.auth.token_data import TokenData, get_current_user
from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE, X_BR_KEY_HEADER
from app.model.action_type import ActionType
from app.model.api_models import ErrorResponse, MallSearchResponse
from app.model.response_helper import error, success
from app.model.search_history import save_search_history
from app.service.search_service import SearchService
from app.utils.logger import api_logger

router = APIRouter()
search_service = SearchService()


@router.get(
    "/search/malls",
    response_model=MallSearchResponse,
    summary="AI-Powered Mall Search",
    description="""
    Search malls using AI-powered natural language processing and Elasticsearch.
    This endpoint allows users to search for malls using natural language queries.
    The AI system will extract search criteria from the query and return relevant malls.
    **Examples of natural language queries:**
    - "Find premium malls with parking in District 1"
    - "Malls under $500 management fee with elevator access"
    - "Shopping centers with high foot traffic near metro stations"
    **Search History:**
    Searches are logged to the search history for analytics when is_new=True (default).
    Set is_new=False to perform searches without saving to database.
    **Authentication:**
    Requires a valid JWT token and X-BR-KEY header for brand identification and search history tracking.
    """,
    responses={
        200: {"description": "Successful search with results", "model": MallSearchResponse},
        401: {"description": "Authentication required or invalid token", "model": ErrorResponse},
        503: {"description": "Elasticsearch service unavailable", "model": ErrorResponse},
    },
    tags=["Elasticsearch Search"],
)
async def search_malls(
    current_user: TokenData = Depends(get_current_user),
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
    x_br_key: Optional[str] = Header(
        None, alias=X_BR_KEY_HEADER, description="Brand identifier for search history tracking", example="brand_67890"
    ),
    is_new: bool = Query(
        default=True,
        description="Whether to save this search to history. Set to false to only query without saving to database",
        example=True,
    ),
):
    """Search booths using AI-powered natural language processing and Elasticsearch"""
    try:
        success_flag, data, error_code, error_message = await search_service.search_booths(
            query=q, page_number=pageNumber, page_size=pageSize, brand_id=x_br_key
        )

        if success_flag:
            if is_new:
                try:
                    save_search_history(
                        user_id=current_user.user_id,
                        brand_id=x_br_key,
                        action_type=ActionType.SEARCH_MALL,
                        search_query=q,
                    )
                except Exception as e:
                    api_logger.warning(f"Failed to save search history: {str(e)}")

            return success(data)
        else:
            return error(error_code, error_message)

    except Exception as e:
        api_logger.error(f"Unexpected error in search for brand {x_br_key}: {str(e)}")
        from app.model.exception_mapper import map_exception_to_error_code

        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)
