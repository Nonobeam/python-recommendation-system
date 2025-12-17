import math
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from app.datastore.brand_repository import BrandRepositoryInstance
from app.datastore.mall_repository import MallRepositoryInstance
from app.datastore.repositories import BrandDemographicDataSource, MallDemographicDataSource
from app.exception.recommendation_exceptions import (
    DemographicsError,
    NoActiveCommissionContractError,
    NoAvailableBoothsError,
)
from app.service.recommendation.scoring import BusinessMatchScorer
from app.utils.logger import api_logger

# Minimum score threshold for a brand to be recommended
MIN_RECOMMENDATION_SCORE = 40


class BrandRecommendationService:
    def __init__(self):
        self.brand_repository = BrandRepositoryInstance
        self.mall_repository = MallRepositoryInstance

    def get_recommended_brands(self, mall_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recommended brands for a mall.

        Args:
            mall_id: Mall identifier
            limit: Number of brands to process (from API pageSize)

        Returns:
            List of brands with score > 40 from the first `limit` brands processed

        Raises:
            NoAvailableBoothsError: If the mall has no available booths
        """
        total_start = time.time()

        # Check if mall has active commission contract before processing
        if not self.mall_repository.has_active_commission_contract(mall_id):
            api_logger.warning(f"Mall {mall_id} has no active commission contract")
            raise NoActiveCommissionContractError(mall_id)

        # Check if mall has available booths before processing
        if not self.mall_repository.has_available_booths(mall_id):
            api_logger.warning(f"Mall {mall_id} has no available booths")
            raise NoAvailableBoothsError(mall_id)

        # Step 1: Get brand IDs (excluding brands with active rentals/requests for this mall)
        t0 = time.time()
        brand_info_map = self.brand_repository.get_simple_brand_info_limited(limit, exclude_for_mall_id=mall_id)
        brand_ids_to_process = list(brand_info_map.keys())
        api_logger.info(
            f"[PROFILE] Brand info fetch (with exclusions): {(time.time() - t0) * 1000:.2f}ms, "
            f"count={len(brand_ids_to_process)}"
        )

        if not brand_ids_to_process:
            api_logger.warning("No active brands found in database (after exclusions)")
            return []

        # Step 2: Run demographics queries in PARALLEL (they don't depend on each other)
        t1 = time.time()
        with ThreadPoolExecutor(max_workers=2) as executor:
            mall_future = executor.submit(MallDemographicDataSource.get_by_id, mall_id)
            brand_demo_future = executor.submit(BrandDemographicDataSource.get_batch, brand_ids_to_process)

            mall_data = mall_future.result()
            brand_data_map = brand_demo_future.result()

        api_logger.info(
            f"[PROFILE] Parallel fetch (mall demo + brand demo): {(time.time() - t1) * 1000:.2f}ms, "
            f"brands_loaded={len(brand_data_map)}"
        )

        if not mall_data:
            raise DemographicsError(
                entity_type="mall",
                entity_id=mall_id,
                message=f"Mall demographics not found for mall_id={mall_id}",
            )

        mall_meta = mall_data.get("meta_data", mall_data)

        t3 = time.time()
        scored_brands = []

        for brand_id in brand_ids_to_process:
            try:
                brand_data = brand_data_map.get(brand_id)
                if not brand_data:
                    continue

                brand_meta = brand_data.get("meta_data", brand_data)

                scorer = BusinessMatchScorer(brand_meta, mall_meta)
                mall_result = scorer.compute_final_score()
                mall_compatibility_score = mall_result.get("final_score", 0)

                if math.isnan(mall_compatibility_score) or mall_compatibility_score is None:
                    continue

                # Only include brands with score > threshold
                if mall_compatibility_score < MIN_RECOMMENDATION_SCORE:
                    continue

                rounded_final_score = math.floor(mall_compatibility_score)

                # Get brand name/logo from already-fetched info
                brand_info = brand_info_map.get(brand_id, {})

                scored_brand = {
                    "brand_id": brand_id,
                    "final_score": rounded_final_score,
                    "brand_name": brand_info.get("brand_name"),
                    "brand_logo": brand_info.get("brand_logo"),
                }
                scored_brands.append(scored_brand)

            except Exception as e:
                api_logger.error(f"Error processing brand {brand_id}: {str(e)}")
                continue

        api_logger.info(f"[PROFILE] Scoring loop: {(time.time() - t3) * 1000:.2f}ms")

        api_logger.info(
            f"[PROFILE] TOTAL: {(time.time() - total_start) * 1000:.2f}ms, "
            f"returned {len(scored_brands)} brands, processed {len(brand_ids_to_process)}"
        )
        return scored_brands
