import uuid
from time import time
from typing import List

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.exception.recommendation_exceptions import (DemographicsError,
                                                     ScoreCalculationError)
from app.service.recommendation.services import (BatchMatchService,
                                                 SingleMatchService)
from app.utils.logger import api_logger
from app.utils.metrics import GLOBAL_METRICS

router = APIRouter()


class SingleMatchRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    mall_id: str = Field(..., description="Mall identifier (UUID)", example="660e8400-e29b-41d4-a716-446655440000")


class BatchMatchRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    mall_ids: List[str] = Field(..., description="List of mall identifiers (UUIDs)", min_items=1)


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@router.post("/recommendations/score")
async def calculate_single_match_score(request: SingleMatchRequest = Body(...)):
    """
    Calculate compatibility score between a brand and a mall based on demographic data.

    Returns detailed score breakdown including:
    - Final compatibility score (0-1)
    - Component scores for each factor
    - Explanations for each component
    - Market interest boost indicator
    """
    try:
        if not is_valid_uuid(request.brand_id):
            raise HTTPException(status_code=400, detail=f"Invalid brand_id format: {request.brand_id}")

        if not is_valid_uuid(request.mall_id):
            raise HTTPException(status_code=400, detail=f"Invalid mall_id format: {request.mall_id}")

        start_time = time()
        service = SingleMatchService()
        result = service.calculate_match_score(request.brand_id, request.mall_id)
        calculation_time = (time() - start_time) * 1000

        GLOBAL_METRICS.record_calculation(calculation_time)
        GLOBAL_METRICS.record_score(result["final_score"])

        return JSONResponse(
            status_code=200,
            content={"success": True, "result": result, "calculation_time_ms": round(calculation_time, 2)},
        )
    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        GLOBAL_METRICS.record_error()
        raise HTTPException(status_code=404, detail=str(e))

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        GLOBAL_METRICS.record_error()
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        api_logger.error(f"Unexpected error in single match: {str(e)}")
        GLOBAL_METRICS.record_error()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/recommendations/batch-score")
async def calculate_batch_match_scores(request: BatchMatchRequest = Body(...)):
    """
    Calculate compatibility scores between a brand and multiple malls.

    Returns ranked list of malls sorted by compatibility score (descending).
    Each result includes detailed component scores and explanations.
    """
    try:
        if not is_valid_uuid(request.brand_id):
            raise HTTPException(status_code=400, detail=f"Invalid brand_id format: {request.brand_id}")

        if not request.mall_ids or len(request.mall_ids) == 0:
            raise HTTPException(status_code=400, detail="mall_ids array cannot be empty")

        for mall_id in request.mall_ids:
            if not is_valid_uuid(mall_id):
                raise HTTPException(status_code=400, detail=f"Invalid mall_id format in array: {mall_id}")

        if len(request.mall_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 mall_ids allowed per batch request")

        service = BatchMatchService()
        results = service.calculate_batch_scores(request.brand_id, request.mall_ids)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "brand_id": request.brand_id,
                "total_evaluated": len(results),
                "results": results,
            },
        )

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        api_logger.error(f"Unexpected error in batch match: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/recommendations/metrics")
async def get_recommendation_metrics():
    """
    Get performance and usage metrics for the recommendation system.

    Returns cache statistics, calculation performance, score distribution, and error counts.
    """
    try:
        return JSONResponse(status_code=200, content={"success": True, "metrics": GLOBAL_METRICS.get_summary()})
    except Exception as e:
        api_logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/recommendations/paginated-batch")
async def calculate_paginated_batch_scores(
    brand_id: str = Query(..., description="Brand identifier (UUID)"),
    mall_ids: str = Query(..., description="Comma-separated mall identifiers (UUIDs)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=50, description="Number of results per page"),
):
    """
    Calculate compatibility scores for multiple malls with pagination support.

    Use comma-separated mall_ids in query parameter for simplicity.
    Returns paginated results sorted by compatibility score.
    """
    try:
        if not is_valid_uuid(brand_id):
            raise HTTPException(status_code=400, detail=f"Invalid brand_id format: {brand_id}")

        mall_id_list = [mid.strip() for mid in mall_ids.split(",")]

        if not mall_id_list:
            raise HTTPException(status_code=400, detail="mall_ids parameter cannot be empty")

        for mall_id in mall_id_list:
            if not is_valid_uuid(mall_id):
                raise HTTPException(status_code=400, detail=f"Invalid mall_id format: {mall_id}")

        service = BatchMatchService()
        results = service.calculate_batch_scores(brand_id, mall_id_list)

        total_results = len(results)
        total_pages = (total_results + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "brand_id": brand_id,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_results": total_results,
                    "total_pages": total_pages,
                    "has_more": page < total_pages,
                },
                "results": paginated_results,
            },
        )

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        api_logger.error(f"Unexpected error in paginated batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
