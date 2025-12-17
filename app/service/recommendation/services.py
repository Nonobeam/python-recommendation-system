from typing import Any, Dict, List

from .scoring import BusinessMatchScorer


class RecommendationService:
    def __init__(self):
        pass


class SingleMatchService(RecommendationService):
    def calculate_match_score(self, brand_id: str, mall_id: str) -> Dict[str, Any]:
        from datetime import datetime

        from app.datastore.repositories import BrandDemographicDataSource, MallDemographicDataSource
        from app.exception.recommendation_exceptions import ScoreCalculationError

        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        mall_data = MallDemographicDataSource.get_by_id(mall_id)
        if not brand_data or not mall_data:
            raise ScoreCalculationError(
                score_type="match_score",
                entity_pair=(brand_id, mall_id),
                message=f"Missing brand_data or mall_data for brand_id={brand_id} and mall_id={mall_id}",
            )
        scorer = BusinessMatchScorer(brand_data.get("meta_data", brand_data), mall_data.get("meta_data", mall_data))
        result = scorer.compute_final_score()
        return {
            "brand_id": brand_id,
            "mall_id": mall_id,
            **result,
            "calculation_timestamp": datetime.now().isoformat(),
        }


class BatchMatchService(RecommendationService):
    def calculate_batch_scores(self, brand_id: str, mall_ids: List[str]) -> List[Dict[str, Any]]:
        from datetime import datetime

        from app.datastore.repositories import BrandDemographicDataSource, MallDemographicDataSource

        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        if not brand_data:
            return [
                {
                    "mall_id": mall_id,
                    "final_score": float("nan"),
                    "component_scores": None,
                    "explanations": None,
                    "calculation_timestamp": datetime.now().isoformat(),
                }
                for mall_id in mall_ids
            ]
        results = []
        for mall_id in mall_ids:
            mall_data = MallDemographicDataSource.get_by_id(mall_id)
            if not mall_data:
                results.append(
                    {
                        "mall_id": mall_id,
                        "final_score": float("nan"),
                        "component_scores": None,
                        "explanations": None,
                        "calculation_timestamp": datetime.now().isoformat(),
                    }
                )
                continue
            scorer = BusinessMatchScorer(brand_data.get("meta_data", brand_data), mall_data.get("meta_data", mall_data))
            result = scorer.compute_final_score()
            results.append(
                {
                    "mall_id": mall_id,
                    **result,
                    "calculation_timestamp": datetime.now().isoformat(),
                }
            )
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results
