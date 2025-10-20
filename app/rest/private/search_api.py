from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from ..config.elasticsearch import AISearchService, ElasticsearchService

router = APIRouter()
elasticsearch_service = ElasticsearchService()
ai_search_service = AISearchService()

@router.get("/search/malls")
async def search_malls(
    q: str = Query(..., description="Natural language search query for malls"),
    size: int = Query(default=10, ge=1, le=100, description="Number of results to return")
):
    """Search malls using AI-powered natural language processing and Elasticsearch"""
    try:
        # Test Elasticsearch connection first
        if not elasticsearch_service.test_connection():
            raise HTTPException(status_code=503, detail="Elasticsearch service unavailable")
        
        # Use the main AI + ELK function
        results = await elasticsearch_service.search_malls_with_ai(q, ai_search_service, size)
        
        if results["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "original_query": results["original_query"],
                    "extracted_criteria": results["extracted_criteria"],
                    "total_found": results["total_found"],
                    "results": results["results"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail=f"Search failed: {results.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing AI-powered search: {str(e)}")

