from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from config.elasticsearch import ElasticsearchService, AISearchService
from utils.logger import api_logger

router = APIRouter()
elasticsearch_service = ElasticsearchService()
ai_search_service = AISearchService()

@router.get("/search/malls")
async def search_malls(
    q: str = Query(..., description="Natural language search query for malls"),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    size: int = Query(default=10, ge=1, le=100, description="Number of results to return")
):
    """Search malls using AI-powered natural language processing and Elasticsearch"""
    try:
        if not elasticsearch_service.test_connection():
            api_logger.error("Elasticsearch service unavailable")
            raise HTTPException(status_code=503, detail="Elasticsearch service unavailable")
        
        api_logger.info(f"Processing AI search query: {q}")
        results = await elasticsearch_service.search_malls_with_ai(q, ai_search_service, page, size)
        
        if results["success"]:
            api_logger.info(f"AI search completed successfully. Found {results.get('total_found', 0)} results on page {page}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "original_query": results["original_query"],
                    "extracted_criteria": results["extracted_criteria"],
                    "pagination": {
                        "current_page": results.get("page", page),
                        "page_size": results.get("size", size),
                        "total_results": results["total_found"],
                        "total_pages": (results["total_found"] + size - 1) // size,  # Ceiling division
                        "has_more": results.get("has_more", False)
                    },
                    "results": results["results"]
                }
            )
        else:
            api_logger.error(f"AI search failed: {results.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"Search failed: {results.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Unexpected error in AI search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing AI-powered search: {str(e)}")

