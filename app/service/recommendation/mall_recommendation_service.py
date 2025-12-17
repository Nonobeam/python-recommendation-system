import math
from typing import Any, Dict, List

from app.datastore.mall_repository import MallRepositoryInstance
from app.datastore.repositories import BrandDemographicDataSource
from app.exception.recommendation_exceptions import DemographicsError
from app.service.recommendation.services import BatchMatchService
from app.utils.logger import api_logger


class MallRecommendationService:
    def __init__(self):
        self.mall_repository = MallRepositoryInstance
        self.batch_match_service = BatchMatchService()

    async def get_recommended_malls(self, brand_id: str) -> List[Dict[str, Any]]:
        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        if not brand_data:
            raise DemographicsError(
                entity_type="brand",
                entity_id=brand_id,
                message=f"Brand demographics not found for brand_id={brand_id}",
            )

        all_mall_ids = self.mall_repository.get_all_active_mall_ids()
        if not all_mall_ids:
            api_logger.warning("No active malls found in database")
            return []

        mall_scores = self.batch_match_service.calculate_batch_scores(brand_id, all_mall_ids)
        mall_scores.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        api_logger.warn(
            f"Scored {len(mall_scores)} malls for brand {brand_id}. "
            f"Sample scores: {[{m.get('mall_id')[:8]: m.get('final_score')} for m in mall_scores[:3]]}"
        )

        valid_mall_scores = [
            mall
            for mall in mall_scores
            if mall.get("final_score") is not None
            and not (isinstance(mall.get("final_score"), float) and math.isnan(mall.get("final_score")))
        ]

        if not valid_mall_scores:
            api_logger.warning(
                f"No compatible malls found for brand_id={brand_id}. "
                f"All {len(mall_scores)} malls returned NaN scores. "
                f"Check mall demographics data quality."
            )
            return []

        mall_ids = [mall.get("mall_id") for mall in valid_mall_scores]
        mall_details = self.mall_repository.get_malls_by_ids(mall_ids)

        scored_malls = []
        for mall_score in valid_mall_scores:
            mall_id = mall_score.get("mall_id")
            mall_detail = mall_details.get(mall_id, {})

            final_score = mall_score.get("final_score", 0)
            rounded_score = math.floor(final_score)

            scored_mall = {
                "mall_id": mall_id,
                "mall_name": mall_detail.get("mall_name"),
                "mall_logo": mall_detail.get("mall_logo"),
                "mall_address": mall_detail.get("mall_address"),
                "final_score": rounded_score,
            }
            scored_malls.append(scored_mall)

        return scored_malls
