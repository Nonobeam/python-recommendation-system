from fastapi import APIRouter, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse
from typing import Optional
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from config.elasticsearch import ElasticsearchService, AISearchService
from auth.token_data import get_current_user, TokenData
from model.api_models import MallSearchResponse, ErrorResponse
from model.search_history import save_search_history
from model.action_type import ActionType
from utils.logger import api_logger
from constants import (
    X_BR_KEY_HEADER, 
    DEFAULT_PAGE_SIZE, 
    MAX_PAGE_SIZE, 
    MIN_PAGE_SIZE
)

router = APIRouter()
elasticsearch_service = ElasticsearchService()
ai_search_service = AISearchService()

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
        200: {
            "description": "Successful search with results",
            "model": MallSearchResponse
        },
        401: {
            "description": "Authentication required or invalid token",
            "model": ErrorResponse
        },
        503: {
            "description": "Elasticsearch service unavailable", 
            "model": ErrorResponse
        }
    },
    tags=["Elasticsearch Search"]
)
async def search_malls(
    current_user: TokenData = Depends(get_current_user),
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
    ),
    x_br_key: Optional[str] = Header(
        None,
        alias=X_BR_KEY_HEADER,
        description="Brand identifier for search history tracking",
        example="brand_67890"
    ),
    is_new: bool = Query(
        default=True,
        description="Whether to save this search to history. Set to false to only query without saving to database",
        example=True
    )
):
    """Search malls using AI-powered natural language processing and Elasticsearch"""
    try:
        if not elasticsearch_service.test_connection():
            api_logger.error("Elasticsearch service unavailable")
            raise HTTPException(status_code=503, detail="Elasticsearch service unavailable")
        
        results = await elasticsearch_service.search_malls_with_ai(x_br_key, q, ai_search_service, page, size)
        
        if results["success"]:
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
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "extracted_criteria": results["extracted_criteria"],
                    "pagination": {
                        "current_page": results.get("page", page),
                        "page_size": results.get("size", size),
                        "total_results": results["total_found"],
                        "total_pages": (results["total_found"] + size - 1) // size,
                        "has_more": results.get("has_more", False)
                    },
                    "results": results["results"]
                }
            )
        else:
            error_msg = results.get('error', 'Unknown error')
            api_logger.error(f"AI search failed for brand {x_br_key}: {error_msg}")
            
            if "Gemini API error: API request failed with status 503" in error_msg:
                raise HTTPException(
                    status_code=503, 
                    detail="AI search service is temporarily unavailable. Please try again later."
                )
            elif "AI extraction failed" in error_msg:
                raise HTTPException(
                    status_code=503, 
                    detail="AI processing service is currently unavailable. Please try again later."
                )
            else:
                raise HTTPException(status_code=500, detail=f"Search failed: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Unexpected error in search for brand {x_br_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing AI-powered search: {str(e)}")


