from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict
from ..service.traffic import get_top_matches, get_matches_for_mall, get_matches_for_business
from ..exception.cache_exceptions import (
    RedisConnectionError, 
    RedisOperationError, 
    CacheError, 
    DemographicDataError, 
    BusinessDataError
)

router = APIRouter()

@router.get("/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top recommendations to return"),
    use_cache: bool = Query(default=True, description="Whether to use cached data")
):
    """Get top N mall-business matches sorted by compatibility score."""
    try:
        recommendations = get_top_matches(limit=limit, use_cache=use_cache)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except DemographicDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing demographic data: {str(e)}")
    except BusinessDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing business data: {str(e)}")
    except RedisConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Cache service unavailable: {str(e)}")
    except RedisOperationError as e:
        raise HTTPException(status_code=500, detail=f"Cache operation failed: {str(e)}")
    except CacheError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/recommendations/mall/{mall_id}")
async def get_recommendations_for_mall(
    mall_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return")
):
    """Get best business matches for a specific mall."""
    try:
        recommendations = get_matches_for_mall(mall_id, limit=limit)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "mall_id": mall_id,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations for mall: {str(e)}")

@router.get("/recommendations/business/{business_id}")
async def get_recommendations_for_business(
    business_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return")
):
    """Get best mall matches for a specific business."""
    try:
        recommendations = get_matches_for_business(business_id, limit=limit)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "business_id": business_id,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations for business: {str(e)}")

# @router.post("/cache/demographics")
# async def calculate_and_cache_demographics():
#     """Calculate and cache all demographics data."""
#     try:
#         from ..datastore.populate_cache import calculate_and_cache_all_demographics
#         result = calculate_and_cache_all_demographics()
#         return JSONResponse(
#             status_code=200,
#             content={
#                 "success": True,
#                 "message": "Demographics calculation completed",
#                 "cached_count": result.get("cached_count", 0)
#             }
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error calculating demographics: {str(e)}")
