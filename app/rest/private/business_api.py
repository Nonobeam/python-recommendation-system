from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.service.traffic import get_top_matches, get_matches_for_mall, get_matches_for_business

router = APIRouter()

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
