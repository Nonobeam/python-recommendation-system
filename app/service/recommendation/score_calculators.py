from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from app.utils.logger import api_logger


class ScoreCalculator(ABC):
    @abstractmethod
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        pass
    
    @abstractmethod
    def get_explanation(self, score: float) -> str:
        pass


class DemographicScoreCalculator(ScoreCalculator):
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        try:
            brand_arr = np.array(brand_vector)
            mall_arr = np.array(mall_vector)
            
            min_length = min(len(brand_arr), len(mall_arr))
            brand_arr = brand_arr[:min_length]
            mall_arr = mall_arr[:min_length]
            
            dot_product = np.dot(brand_arr, mall_arr)
            brand_magnitude = np.linalg.norm(brand_arr)
            mall_magnitude = np.linalg.norm(mall_arr)
            
            if brand_magnitude == 0 or mall_magnitude == 0:
                return 0.0
            
            cosine_similarity = dot_product / (brand_magnitude * mall_magnitude)
            
            return max(0.0, min(1.0, cosine_similarity))
        except Exception as e:
            api_logger.error(f"Error calculating demographic score: {str(e)}")
            return 0.0
    
    def get_explanation(self, score: float) -> str:
        if score >= 0.8:
            return "Excellent demographic match - brand and mall profiles are highly aligned"
        elif score >= 0.6:
            return "Good demographic match - profiles show strong compatibility"
        elif score >= 0.4:
            return "Moderate demographic match - some alignment with potential gaps"
        else:
            return "Poor demographic match - significant profile differences"


class BudgetCompatibilityCalculator(ScoreCalculator):
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        try:
            if not brand_data or not mall_data:
                return 0.5
            
            meta_data = brand_data.get("meta_data", brand_data)
            financial_capacity = meta_data.get("financial_capacity", {})
            brand_max_rent = financial_capacity.get("max_affordable_rent", 0)
            
            mall_meta = mall_data.get("meta_data", mall_data)
            tenant_mix = mall_meta.get("tenant_mix", {})
            mall_avg_price = tenant_mix.get("avg_price", 0)
            
            if brand_max_rent == 0 or mall_avg_price == 0:
                return 0.5
            
            ratio = brand_max_rent / mall_avg_price
            
            if 0.9 <= ratio <= 1.3:
                return 1.0
            elif 0.7 <= ratio < 0.9 or 1.3 < ratio <= 1.5:
                return 0.8
            elif 0.5 <= ratio < 0.7 or 1.5 < ratio <= 2.0:
                return 0.5
            else:
                return max(0.0, 1.0 - abs(ratio - 1.0) / 2.0)
                
        except Exception as e:
            api_logger.error(f"Error calculating budget compatibility: {str(e)}")
            return 0.5
    
    def get_explanation(self, score: float) -> str:
        if score >= 0.8:
            return "Budget alignment is strong - brand can comfortably afford this location"
        elif score >= 0.5:
            return "Budget compatibility is moderate - some financial adjustment may be needed"
        else:
            return "Budget mismatch - significant gap between brand capacity and mall pricing"


class TrafficCompatibilityCalculator(ScoreCalculator):
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        try:
            if not brand_data or not mall_data:
                return 0.5
            
            meta_data = brand_data.get("meta_data", brand_data)
            requirements = meta_data.get("requirements", {})
            brand_min_traffic = requirements.get("min_traffic_needed", 0)
            
            mall_meta = mall_data.get("meta_data", mall_data)
            market_intelligence = mall_meta.get("market_intelligence", {})
            mall_traffic = market_intelligence.get("avg_daily_visitors", 0)
            
            if brand_min_traffic == 0:
                return 0.7
            if mall_traffic == 0:
                return 0.0
            
            ratio = mall_traffic / brand_min_traffic
            
            if 1.1 <= ratio <= 1.3:
                return 1.0
            elif 0.9 <= ratio < 1.1 or 1.3 < ratio <= 1.5:
                return 0.9
            elif 0.7 <= ratio < 0.9 or 1.5 < ratio <= 2.0:
                return 0.7
            elif 0.5 <= ratio < 0.7:
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            api_logger.error(f"Error calculating traffic compatibility: {str(e)}")
            return 0.5
    
    def get_explanation(self, score: float) -> str:
        if score >= 0.8:
            return "Traffic patterns align well - mall visitor volume meets brand requirements"
        elif score >= 0.5:
            return "Traffic compatibility is moderate - may need strategic positioning"
        else:
            return "Traffic mismatch - mall volume may not meet brand visitor needs"


class HistoricalPerformanceCalculator(ScoreCalculator):
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        try:
            if not brand_data or not mall_data:
                return 0.5
            
            brand_meta = brand_data.get("meta_data", brand_data)
            brand_track_record = brand_meta.get("historical_track_record", {})
            brand_success_rate = 0.0
            if brand_track_record.get("total_locations", 0) > 0:
                brand_success_rate = brand_track_record.get("successful_locations", 0) / brand_track_record.get("total_locations", 1)
            
            brand_avg_duration = brand_track_record.get("avg_location_duration_months", 0.0)
            
            mall_meta = mall_data.get("meta_data", mall_data)
            mall_historical = mall_meta.get("historical_performance", {})
            mall_success_rate = mall_historical.get("success_rate", 50.0) / 100.0
            
            brand_score = (brand_success_rate * 0.7) + (min(brand_avg_duration / 60.0, 1.0) * 0.3)
            
            combined_score = (brand_score * 0.6) + (mall_success_rate * 0.4)
            
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            api_logger.error(f"Error calculating historical performance: {str(e)}")
            return 0.5
    
    def get_explanation(self, score: float) -> str:
        if score >= 0.7:
            return "Strong historical performance - brand and mall both show success patterns"
        elif score >= 0.5:
            return "Moderate historical performance - some proven success with gaps"
        else:
            return "Limited historical success - may require careful planning and support"


class TenantMixCompatibilityCalculator(ScoreCalculator):
    def calculate(self, brand_vector: List[float], mall_vector: List[float], brand_data: Dict[str, Any] = None, mall_data: Dict[str, Any] = None) -> float:
        try:
            if not brand_data or not mall_data:
                return 0.5
            
            brand_meta = brand_data.get("meta_data", brand_data)
            business_profile = brand_meta.get("business_profile", {})
            brand_category = business_profile.get("category", "unknown")
            
            mall_meta = mall_data.get("meta_data", mall_data)
            tenant_mix = mall_meta.get("tenant_mix", {})
            
            if brand_category == "food" or brand_category == "dining":
                category_percent = tenant_mix.get("food_percent", 0.0)
            elif brand_category == "service":
                category_percent = tenant_mix.get("service_percent", 0.0)
            elif brand_category == "shop" or brand_category == "retail":
                category_percent = tenant_mix.get("shop_percent", 0.0)
            else:
                return 0.7
            
            if category_percent < 20:
                return 1.0
            elif category_percent < 35:
                return 0.8
            elif category_percent < 50:
                return 0.6
            elif category_percent < 65:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            api_logger.error(f"Error calculating tenant mix compatibility: {str(e)}")
            return 0.5
    
    def get_explanation(self, score: float) -> str:
        if score >= 0.7:
            return "Good tenant mix fit - category has room for growth in this mall"
        elif score >= 0.4:
            return "Moderate tenant mix - category is present but not saturated"
        else:
            return "Tenant mix concern - category may be reaching saturation point"


class WeightedScoreAggregator:
    def __init__(self, weights: Dict[str, float] = None):
        default_weights = {
            "demographic": 0.25,
            "budget": 0.20,
            "traffic": 0.20,
            "historical": 0.20,
            "tenant_mix": 0.15
        }
        self.weights = weights or default_weights
        
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            api_logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.weights = {k: v / total_weight for k, v in self.weights.items()}
    
    def aggregate(
        self,
        demographic_score: float,
        budget_score: float,
        traffic_score: float,
        historical_score: float,
        tenant_mix_score: float,
        market_interest_boost: float = 1.0
    ) -> float:
        weighted_sum = (
            demographic_score * self.weights["demographic"] +
            budget_score * self.weights["budget"] +
            traffic_score * self.weights["traffic"] +
            historical_score * self.weights["historical"] +
            tenant_mix_score * self.weights["tenant_mix"]
        )
        
        final_score = weighted_sum * market_interest_boost
        
        return max(0.0, min(1.0, final_score))
    
    def get_component_scores(
        self,
        demographic_score: float,
        budget_score: float,
        traffic_score: float,
        historical_score: float,
        tenant_mix_score: float
    ) -> Dict[str, float]:
        return {
            "demographic": demographic_score,
            "budget": budget_score,
            "traffic": traffic_score,
            "historical": historical_score,
            "tenant_mix": tenant_mix_score
        }
