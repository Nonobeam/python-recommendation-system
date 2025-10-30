from typing import List, Dict, Any, Optional
from datetime import datetime
from .repositories import BrandDemographicDataSource, MallDemographicDataSource
from .vector_builders import MallVectorBuilder, BrandVectorBuilder, VectorNormalizer
from .score_calculators import (
    DemographicScoreCalculator,
    BudgetCompatibilityCalculator,
    TrafficCompatibilityCalculator,
    HistoricalPerformanceCalculator,
    TenantMixCompatibilityCalculator,
    WeightedScoreAggregator
)
from app.exception.recommendation_exceptions import ScoreCalculationError, DemographicsError
from app.utils.logger import api_logger


class RecommendationService:
    def __init__(
        self,
        brand_data_source: BrandDemographicDataSource = None,
        mall_data_source: MallDemographicDataSource = None,
        mall_vector_builder: MallVectorBuilder = None,
        brand_vector_builder: BrandVectorBuilder = None,
        vector_normalizer: VectorNormalizer = None,
        demographic_calculator: DemographicScoreCalculator = None,
        budget_calculator: BudgetCompatibilityCalculator = None,
        traffic_calculator: TrafficCompatibilityCalculator = None,
        historical_calculator: HistoricalPerformanceCalculator = None,
        tenant_mix_calculator: TenantMixCompatibilityCalculator = None,
        score_aggregator: WeightedScoreAggregator = None
    ):
        self.brand_data_source = brand_data_source or BrandDemographicDataSource
        self.mall_data_source = mall_data_source or MallDemographicDataSource
        self.mall_vector_builder = mall_vector_builder or MallVectorBuilder()
        self.brand_vector_builder = brand_vector_builder or BrandVectorBuilder()
        self.vector_normalizer = vector_normalizer or VectorNormalizer(14)
        self.demographic_calculator = demographic_calculator or DemographicScoreCalculator()
        self.budget_calculator = budget_calculator or BudgetCompatibilityCalculator()
        self.traffic_calculator = traffic_calculator or TrafficCompatibilityCalculator()
        self.historical_calculator = historical_calculator or HistoricalPerformanceCalculator()
        self.tenant_mix_calculator = tenant_mix_calculator or TenantMixCompatibilityCalculator()
        self.score_aggregator = score_aggregator or WeightedScoreAggregator()


class SingleMatchService(RecommendationService):
    def calculate_match_score(
        self,
        brand_id: str,
        mall_id: str
    ) -> Dict[str, Any]:
        try:
            brand_data = self.brand_data_source.get_by_id(brand_id)
            if not brand_data:
                raise DemographicsError(
                    f"Brand demographic data not found for brand_id: {brand_id}"
                )
            
            mall_data = self.mall_data_source.get_by_id(mall_id)
            if not mall_data:
                raise DemographicsError(
                    f"Mall demographic data not found for mall_id: {mall_id}"
                )
            
            brand_vector = self.brand_vector_builder.build(brand_data)
            mall_vector = self.mall_vector_builder.build(mall_data)
            
            brand_vector_normalized = self.vector_normalizer.normalize(brand_vector)
            mall_vector_normalized = self.vector_normalizer.normalize(mall_vector)
            
            demographic_score = self.demographic_calculator.calculate(
                brand_vector_normalized,
                mall_vector_normalized,
                brand_data,
                mall_data
            )
            
            budget_score = self.budget_calculator.calculate(
                brand_vector_normalized,
                mall_vector_normalized,
                brand_data,
                mall_data
            )
            
            traffic_score = self.traffic_calculator.calculate(
                brand_vector_normalized,
                mall_vector_normalized,
                brand_data,
                mall_data
            )
            
            historical_score = self.historical_calculator.calculate(
                brand_vector_normalized,
                mall_vector_normalized,
                brand_data,
                mall_data
            )
            
            tenant_mix_score = self.tenant_mix_calculator.calculate(
                brand_vector_normalized,
                mall_vector_normalized,
                brand_data,
                mall_data
            )
            
            market_interest_boost = 1.0
            brand_meta = brand_data.get("meta_data", brand_data)
            market_signals = brand_meta.get("market_fit_signals", {})
            if market_signals.get("interest_from_mall_owners", 0) > 0 or market_signals.get("offers_received", 0) > 0:
                market_interest_boost = 1.05
            
            final_score = self.score_aggregator.aggregate(
                demographic_score,
                budget_score,
                traffic_score,
                historical_score,
                tenant_mix_score,
                market_interest_boost
            )
            
            component_scores = self.score_aggregator.get_component_scores(
                demographic_score,
                budget_score,
                traffic_score,
                historical_score,
                tenant_mix_score
            )
            
            explanations = {
                "demographic": self.demographic_calculator.get_explanation(demographic_score),
                "budget": self.budget_calculator.get_explanation(budget_score),
                "traffic": self.traffic_calculator.get_explanation(traffic_score),
                "historical": self.historical_calculator.get_explanation(historical_score),
                "tenant_mix": self.tenant_mix_calculator.get_explanation(tenant_mix_score)
            }
            
            return {
                "brand_id": brand_id,
                "mall_id": mall_id,
                "final_score": round(final_score, 4),
                "component_scores": component_scores,
                "explanations": explanations,
                "calculation_timestamp": datetime.now().isoformat(),
                "market_interest_boost_applied": market_interest_boost > 1.0
            }
            
        except DemographicsError as e:
            api_logger.error(f"Demographics error in single match: {str(e)}")
            raise
        except Exception as e:
            api_logger.error(f"Error calculating match score: {str(e)}")
            raise ScoreCalculationError(f"Failed to calculate match score: {str(e)}")


class BatchMatchService(RecommendationService):
    def calculate_batch_scores(
        self,
        brand_id: str,
        mall_ids: List[str]
    ) -> List[Dict[str, Any]]:
        try:
            brand_data = self.brand_data_source.get_by_id(brand_id)
            if not brand_data:
                raise DemographicsError(
                    f"Brand demographic data not found for brand_id: {brand_id}"
                )
            
            brand_vector = self.brand_vector_builder.build(brand_data)
            brand_vector_normalized = self.vector_normalizer.normalize(brand_vector)
            
            results = []
            
            for mall_id in mall_ids:
                try:
                    mall_data = self.mall_data_source.get_by_id(mall_id)
                    if not mall_data:
                        api_logger.warning(f"Mall demographic data not found for mall_id: {mall_id}")
                        continue
                    
                    mall_vector = self.mall_vector_builder.build(mall_data)
                    mall_vector_normalized = self.vector_normalizer.normalize(mall_vector)
                    
                    demographic_score = self.demographic_calculator.calculate(
                        brand_vector_normalized,
                        mall_vector_normalized,
                        brand_data,
                        mall_data
                    )
                    
                    budget_score = self.budget_calculator.calculate(
                        brand_vector_normalized,
                        mall_vector_normalized,
                        brand_data,
                        mall_data
                    )
                    
                    traffic_score = self.traffic_calculator.calculate(
                        brand_vector_normalized,
                        mall_vector_normalized,
                        brand_data,
                        mall_data
                    )
                    
                    historical_score = self.historical_calculator.calculate(
                        brand_vector_normalized,
                        mall_vector_normalized,
                        brand_data,
                        mall_data
                    )
                    
                    tenant_mix_score = self.tenant_mix_calculator.calculate(
                        brand_vector_normalized,
                        mall_vector_normalized,
                        brand_data,
                        mall_data
                    )
                    
                    market_interest_boost = 1.0
                    brand_meta = brand_data.get("meta_data", brand_data)
                    market_signals = brand_meta.get("market_fit_signals", {})
                    if market_signals.get("interest_from_mall_owners", 0) > 0 or market_signals.get("offers_received", 0) > 0:
                        market_interest_boost = 1.05
                    
                    final_score = self.score_aggregator.aggregate(
                        demographic_score,
                        budget_score,
                        traffic_score,
                        historical_score,
                        tenant_mix_score,
                        market_interest_boost
                    )
                    
                    component_scores = self.score_aggregator.get_component_scores(
                        demographic_score,
                        budget_score,
                        traffic_score,
                        historical_score,
                        tenant_mix_score
                    )
                    
                    explanations = {
                        "demographic": self.demographic_calculator.get_explanation(demographic_score),
                        "budget": self.budget_calculator.get_explanation(budget_score),
                        "traffic": self.traffic_calculator.get_explanation(traffic_score),
                        "historical": self.historical_calculator.get_explanation(historical_score),
                        "tenant_mix": self.tenant_mix_calculator.get_explanation(tenant_mix_score)
                    }
                    
                    results.append({
                        "mall_id": mall_id,
                        "final_score": round(final_score, 4),
                        "component_scores": component_scores,
                        "explanations": explanations
                    })
                    
                except Exception as e:
                    api_logger.error(f"Error processing mall {mall_id}: {str(e)}")
                    continue
            
            results.sort(key=lambda x: x["final_score"], reverse=True)
            
            return results
            
        except DemographicsError as e:
            api_logger.error(f"Demographics error in batch match: {str(e)}")
            raise
        except Exception as e:
            api_logger.error(f"Error calculating batch scores: {str(e)}")
            raise ScoreCalculationError(f"Failed to calculate batch scores: {str(e)}")


class CacheInvalidationService:
    def __init__(
        self,
        brand_data_source: BrandDemographicDataSource = None,
        mall_data_source: MallDemographicDataSource = None
    ):
        self.brand_data_source = brand_data_source or BrandDemographicDataSource
        self.mall_data_source = mall_data_source or MallDemographicDataSource
    
    def invalidate_brand_cache(self, brand_id: str):
        try:
            self.brand_data_source.redis_repo.store(brand_id, None, 0)
            api_logger.info(f"Invalidated brand cache for brand_id: {brand_id}")
        except Exception as e:
            api_logger.error(f"Error invalidating brand cache: {str(e)}")
    
    def invalidate_mall_cache(self, mall_id: str):
        try:
            self.mall_data_source.redis_repo.store(mall_id, None, 0)
            api_logger.info(f"Invalidated mall cache for mall_id: {mall_id}")
        except Exception as e:
            api_logger.error(f"Error invalidating mall cache: {str(e)}")
