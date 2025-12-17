import uuid
from time import time
from typing import List

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from app.exception.recommendation_exceptions import (
    DemographicsError,
    NoActiveCommissionContractError,
    NoAvailableBoothsError,
    ScoreCalculationError,
)
from app.model.booth_recommendation_models import BoothRecommendationItem, BoothRecommendationResponse
from app.model.brand_recommendation_models import BrandRecommendationItem, BrandRecommendationResponse
from app.model.error_code import ErrorCode
from app.model.exception_mapper import map_exception_to_error_code
from app.model.mall_recommendation_models import MallRecommendationItem, MallRecommendationResponse
from app.model.response_helper import error, success
from app.service.recommendation.booth_recommendation_service import BoothRecommendationService
from app.service.recommendation.brand_recommendation_service import BrandRecommendationService
from app.service.recommendation.mall_recommendation_service import MallRecommendationService
from app.service.recommendation.services import BatchMatchService, SingleMatchService
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
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brand_id format: {request.brand_id}")

        if not is_valid_uuid(request.mall_id):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid mall_id format: {request.mall_id}")

        start_time = time()
        service = SingleMatchService()
        result = service.calculate_match_score(request.brand_id, request.mall_id)
        calculation_time = (time() - start_time) * 1000

        GLOBAL_METRICS.record_calculation(calculation_time)
        GLOBAL_METRICS.record_score(result["final_score"])

        response_data = {"result": result, "calculation_time_ms": round(calculation_time, 2)}
        return success(response_data)
    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        GLOBAL_METRICS.record_error()
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        GLOBAL_METRICS.record_error()
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in single match: {str(e)}")
        GLOBAL_METRICS.record_error()
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.post("/recommendations/batch-score")
async def calculate_batch_match_scores(request: BatchMatchRequest = Body(...)):
    """
    Calculate compatibility scores between a brand and multiple malls.

    Returns ranked list of malls sorted by compatibility score (descending).
    Each result includes detailed component scores and explanations.
    """
    try:
        if not is_valid_uuid(request.brand_id):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brand_id format: {request.brand_id}")

        if not request.mall_ids or len(request.mall_ids) == 0:
            return error(ErrorCode.VALIDATION_ERROR, "mall_ids array cannot be empty")

        for mall_id in request.mall_ids:
            if not is_valid_uuid(mall_id):
                return error(ErrorCode.VALIDATION_ERROR, f"Invalid mall_id format in array: {mall_id}")

        if len(request.mall_ids) > 100:
            return error(ErrorCode.VALIDATION_ERROR, "Maximum 100 mall_ids allowed per batch request")

        service = BatchMatchService()
        results = service.calculate_batch_scores(request.brand_id, request.mall_ids)

        response_data = {
            "brand_id": request.brand_id,
            "total_evaluated": len(results),
            "results": results,
        }
        return success(response_data)

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in batch match: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.get("/recommendations/metrics")
async def get_recommendation_metrics():
    """
    Get performance and usage metrics for the recommendation system.

    Returns cache statistics, calculation performance, score distribution, and error counts.
    """
    try:
        response_data = {"metrics": GLOBAL_METRICS.get_summary()}
        return success(response_data)
    except Exception as e:
        api_logger.error(f"Error retrieving metrics: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


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
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brand_id format: {brand_id}")

        mall_id_list = [mid.strip() for mid in mall_ids.split(",")]

        if not mall_id_list:
            return error(ErrorCode.VALIDATION_ERROR, "mall_ids parameter cannot be empty")

        for mall_id in mall_id_list:
            if not is_valid_uuid(mall_id):
                return error(ErrorCode.VALIDATION_ERROR, f"Invalid mall_id format: {mall_id}")

        service = BatchMatchService()
        results = service.calculate_batch_scores(brand_id, mall_id_list)

        total_results = len(results)
        total_pages = (total_results + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        response_data = {
            "brand_id": brand_id,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_results": total_results,
                "total_pages": total_pages,
                "has_more": page < total_pages,
            },
            "results": paginated_results,
        }
        return success(response_data)

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in paginated batch: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.get("/recommendations/booths")
async def get_recommended_booths(
    brandId: str = Query(..., description="Brand identifier (UUID)"),
    pageNumber: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of results per page"),
):
    """
    Get recommended booths across all malls for a brand.

    Filter parameters are automatically extracted from:
    - Brand demographics (financial capacity, operational profile, requirements)
    - Brand search history (using AI to infer preferences)

    Returns ranked list of booths sorted by composite score (descending).
    Each result includes booth details, mall details, scores, and explanations.
    """
    try:
        if not is_valid_uuid(brandId):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brandId format: {brandId}")

        service = BoothRecommendationService()
        all_results = await service.get_recommended_booths(brandId)

        total_results = len(all_results)
        total_pages = (total_results + pageSize - 1) // pageSize if total_results > 0 else 0
        start_idx = (pageNumber - 1) * pageSize
        end_idx = start_idx + pageSize
        paginated_results = all_results[start_idx:end_idx]

        response_data = BoothRecommendationResponse(
            brand_id=brandId,
            total_results=total_results,
            page=pageNumber,
            page_size=pageSize,
            total_pages=total_pages,
            has_more=pageNumber < total_pages,
            results=[BoothRecommendationItem(**item) for item in paginated_results],
        )

        return success(response_data.dict())

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in booth recommendations: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.get("/recommendations/booths/mall/{mallId}")
async def get_recommended_booths_by_mall(
    mallId: str,
    brandId: str = Query(..., description="Brand identifier (UUID)"),
    pageNumber: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of results per page"),
):
    """
    Get recommended booths for a specific mall and brand.

    Filter parameters are automatically extracted from:
    - Brand demographics (financial capacity, operational profile, requirements)
    - Brand search history (using AI to infer preferences)

    Returns ranked list of booths sorted by composite score (descending).
    Each result includes booth details, scores, and explanations.
    """
    try:
        if not is_valid_uuid(brandId):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brandId format: {brandId}")

        if not is_valid_uuid(mallId):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid mallId format: {mallId}")

        service = BoothRecommendationService()
        all_results = await service.get_recommended_booths_by_mall(brandId, mallId)

        total_results = len(all_results)
        total_pages = (total_results + pageSize - 1) // pageSize if total_results > 0 else 0
        start_idx = (pageNumber - 1) * pageSize
        end_idx = start_idx + pageSize
        paginated_results = all_results[start_idx:end_idx]

        response_data = BoothRecommendationResponse(
            brand_id=brandId,
            total_results=total_results,
            page=pageNumber,
            page_size=pageSize,
            total_pages=total_pages,
            has_more=pageNumber < total_pages,
            results=[BoothRecommendationItem(**item) for item in paginated_results],
        )

        return success(response_data.dict())

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in booth recommendations by mall: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.get("/recommendations/malls")
async def get_recommended_malls(
    brandId: str = Query(..., description="Brand identifier (UUID)"),
    pageNumber: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of results per page"),
):
    """
    Get recommended malls for a brand.

    Filter parameters are automatically extracted from:
    - Brand demographics (financial capacity, operational profile, requirements)
    - Brand search history (using AI to infer preferences)

    Returns ranked list of malls sorted by compatibility score (descending).
    Each result includes mall details, scores, and explanations.
    """
    try:
        if not is_valid_uuid(brandId):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid brandId format: {brandId}")

        service = MallRecommendationService()
        all_results = await service.get_recommended_malls(brandId)

        total_results = len(all_results)
        total_pages = (total_results + pageSize - 1) // pageSize if total_results > 0 else 0
        start_idx = (pageNumber - 1) * pageSize
        end_idx = start_idx + pageSize
        paginated_results = all_results[start_idx:end_idx]

        response_data = MallRecommendationResponse(
            brand_id=brandId,
            total_results=total_results,
            page=pageNumber,
            page_size=pageSize,
            total_pages=total_pages,
            has_more=pageNumber < total_pages,
            results=[MallRecommendationItem(**item) for item in paginated_results],
        )

        return success(response_data.dict())

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in mall recommendations: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)


@router.get("/recommendations/brands")
async def get_recommended_brands(
    mallId: str = Query(..., description="Mall identifier (UUID)"),
    pageNumber: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of results per page"),
):
    """
    Get recommended brands for a mall.

    Scoring considers:
    - Brand-mall compatibility (demographics match)
    - Available booths in the mall that match brand requirements
    - Best booth match score for each brand

    Returns ranked list of brands sorted by composite score (descending).
    Each result includes brand details, scores, and explanations.
    """
    try:
        if not is_valid_uuid(mallId):
            return error(ErrorCode.VALIDATION_ERROR, f"Invalid mallId format: {mallId}")

        service = BrandRecommendationService()
        # Pass pageSize as limit - service will return at most this many brands
        results = service.get_recommended_brands(mallId, limit=pageSize)

        total_results = len(results)

        response_data = BrandRecommendationResponse(
            mall_id=mallId,
            total_results=total_results,
            page=1,  # Always page 1 with early-exit pagination
            page_size=pageSize,
            total_pages=1 if total_results > 0 else 0,
            has_more=False,  # Early-exit returns all qualifying brands up to limit
            results=[BrandRecommendationItem(**item) for item in results],
        )

        return success(response_data.dict())

    except NoAvailableBoothsError as e:
        api_logger.warning(f"No available booths error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except NoActiveCommissionContractError as e:
        api_logger.warning(f"No active commission contract error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except DemographicsError as e:
        api_logger.warning(f"Demographics error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except ScoreCalculationError as e:
        api_logger.error(f"Score calculation error: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)

    except Exception as e:
        api_logger.error(f"Unexpected error in brand recommendations: {str(e)}")
        error_code, message = map_exception_to_error_code(e)
        return error(error_code, message)
