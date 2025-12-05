import math
from typing import Any, Dict, List

from app.exception.recommendation_exceptions import DemographicsError
from app.service.recommendation.booth_filter_extractor import BoothFilterExtractor
from app.service.recommendation.booth_repository import BoothRepositoryInstance
from app.service.recommendation.brand_repository import BrandRepositoryInstance
from app.service.recommendation.repositories import BrandDemographicDataSource, MallDemographicDataSource
from app.service.recommendation.scoring import BoothScorer, BusinessMatchScorer
from app.service.recommendation.scoring.score_calculator import calculate_brand_recommendation_score
from app.utils.logger import api_logger


class BrandRecommendationService:
    def __init__(self):
        self.brand_repository = BrandRepositoryInstance
        self.booth_repository = BoothRepositoryInstance
        self.filter_extractor = BoothFilterExtractor()

    async def get_recommended_brands(self, mall_id: str) -> List[Dict[str, Any]]:
        mall_data = MallDemographicDataSource.get_by_id(mall_id)
        if not mall_data:
            raise DemographicsError(
                entity_type="mall",
                entity_id=mall_id,
                message=f"Mall demographics not found for mall_id={mall_id}",
            )

        mall_meta = mall_data.get("meta_data", mall_data)

        all_brand_ids = self.brand_repository.get_all_active_brand_ids()
        if not all_brand_ids:
            api_logger.warning("No active brands found in database")
            return []

        scored_brands = []
        for brand_id in all_brand_ids:
            try:
                brand_data = BrandDemographicDataSource.get_by_id(brand_id)
                if not brand_data:
                    continue

                brand_meta = brand_data.get("meta_data", brand_data)

                scorer = BusinessMatchScorer(brand_meta, mall_meta)
                mall_result = scorer.compute_final_score()
                mall_compatibility_score = mall_result.get("final_score", 0)

                if math.isnan(mall_compatibility_score) or mall_compatibility_score is None:
                    continue

                filters = await self.filter_extractor.extract_filters_from_brand(brand_id)

                min_size = filters.get("min_size")
                max_size = filters.get("max_size")
                max_price = filters.get("max_price")
                category_id = filters.get("category_id")
                preferred_floors = filters.get("preferred_floors")

                booths = self.booth_repository.get_available_booths_by_mall_id(
                    mall_id=mall_id,
                    min_size=min_size,
                    max_size=max_size,
                    max_price=max_price,
                    category_id=category_id,
                    preferred_floors=preferred_floors,
                )

                available_booths_count = len(booths) if booths else 0

                booth_match_score = None
                best_booth_score = 0

                if booths:
                    for booth in booths:
                        booth_id = booth.get("booth_id")
                        try:
                            booth_for_scoring = booth.copy()
                            if booth_id:
                                details = self.booth_repository.get_booth_with_details(booth_id)
                                if details:
                                    booth_for_scoring.update(details)

                            booth_scorer = BoothScorer(brand_meta, booth_for_scoring, mall_compatibility_score)
                            booth_result = booth_scorer.compute_final_score()
                            composite_score = booth_result.get("composite_score", 0)

                            if composite_score > best_booth_score:
                                best_booth_score = composite_score
                                booth_match_score = composite_score
                        except Exception as e:
                            api_logger.error(f"Error scoring booth {booth_id} for brand {brand_id}: {str(e)}")
                            continue

                final_score = calculate_brand_recommendation_score(
                    mall_compatibility_score, booth_match_score, available_booths_count
                )
                rounded_final_score = math.floor(final_score)

                scored_brand = {
                    "brand_id": brand_id,
                    "final_score": rounded_final_score,
                    "mall_compatibility_score": mall_compatibility_score,
                    "booth_match_score": booth_match_score,
                    "available_booths_count": available_booths_count,
                }
                scored_brands.append(scored_brand)
            except Exception as e:
                api_logger.error(f"Error processing brand {brand_id}: {str(e)}")
                continue

        scored_brands.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        brand_ids = [brand.get("brand_id") for brand in scored_brands]
        brand_details = self.brand_repository.get_brands_by_ids(brand_ids)

        for scored_brand in scored_brands:
            brand_id = scored_brand.get("brand_id")
            brand_detail = brand_details.get(brand_id, {})
            scored_brand["brand_name"] = brand_detail.get("brand_name")
            scored_brand["brand_logo"] = brand_detail.get("brand_logo")

        return scored_brands
