from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np
from app.utils.logger import api_logger


class VectorBuilder(ABC):
    @abstractmethod
    def build(self, demographic_data: Dict[str, Any]) -> List[float]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        pass


class MallVectorBuilder(VectorBuilder):
    def __init__(self):
        self.feature_names = [
            "shop_percent", "food_percent", "service_percent",
            "occupancy_rate", "avg_traffic_per_zone",
            "tenant_success_rate", "avg_tenant_duration_months", "tenant_turnover_rate",
            "competition_nearby", "accessibility_score", "catchment_area_population",
            "verification_status", "days_since_verification"
        ]
    
    def get_dimension(self) -> int:
        return len(self.feature_names)
    
    def get_feature_names(self) -> List[str]:
        return self.feature_names
    
    def build(self, demographic_data: Dict[str, Any]) -> List[float]:
        try:
            meta_data = demographic_data.get("meta_data", demographic_data)
            
            tenant_mix = meta_data.get("tenant_mix", {})
            zone_performance = meta_data.get("zone_performance", {})
            historical_performance = meta_data.get("historical_performance", {})
            market_intelligence = meta_data.get("market_intelligence", {})
            verified_data = meta_data.get("verified_data", {})
            
            vector = []
            
            vector.append(tenant_mix.get("shop_percent", 0.0))
            vector.append(tenant_mix.get("food_percent", 0.0))
            vector.append(tenant_mix.get("service_percent", 0.0))
            
            vector.append(zone_performance.get("occupancy_rate", 0.0))
            vector.append(zone_performance.get("avg_traffic_per_zone", 0.0))
            
            vector.append(historical_performance.get("tenant_success_rate", 0.0))
            vector.append(historical_performance.get("avg_tenant_duration_months", 0.0))
            vector.append(historical_performance.get("tenant_turnover_rate", 0.0))
            
            competition = market_intelligence.get("competition_nearby", 0)
            vector.append(1.0 if competition else 0.0)
            vector.append(market_intelligence.get("accessibility_score", 0.0))
            vector.append(market_intelligence.get("catchment_area_population", 0.0))
            
            verification_status = verified_data.get("verification_status", "unverified")
            vector.append(1.0 if verification_status == "verified" else 0.0)
            
            last_verification = verified_data.get("last_verification_date")
            days_since = 365.0
            if last_verification:
                try:
                    from datetime import datetime
                    verification_date = datetime.fromisoformat(last_verification.replace('Z', '+00:00'))
                    days_since = (datetime.now().replace(tzinfo=verification_date.tzinfo) - verification_date).days
                except:
                    days_since = 365.0
            vector.append(min(days_since / 365.0, 1.0))
            
            return vector
            
        except Exception as e:
            api_logger.error(f"Error building mall vector: {str(e)}")
            return [0.0] * self.get_dimension()


class BrandVectorBuilder(VectorBuilder):
    def __init__(self):
        self.feature_names = [
            "avg_daily_revenue", "avg_transaction_value", "transaction_frequency", "revenue_per_sqm",
            "budget_normalized", "max_affordable_rent_normalized", "rent_to_income_ratio",
            "min_traffic_needed", "requires_kitchen", "requires_ventilation", "preferred_zones_count",
            "staff_count", "operating_hours_match",
            "interest_from_mall_owners", "offers_received", "negotiation_stage_count",
            "total_locations", "successful_locations", "avg_location_duration_months"
        ]
    
    def get_dimension(self) -> int:
        return len(self.feature_names)
    
    def get_feature_names(self) -> List[str]:
        return self.feature_names
    
    def build(self, demographic_data: Dict[str, Any]) -> List[float]:
        try:
            meta_data = demographic_data.get("meta_data", demographic_data)
            
            proven_performance = meta_data.get("proven_performance", {})
            financial_capacity = meta_data.get("financial_capacity", {})
            requirements = meta_data.get("requirements", {})
            business_profile = meta_data.get("business_profile", {})
            market_fit_signals = meta_data.get("market_fit_signals", {})
            historical_track_record = meta_data.get("historical_track_record", {})
            
            vector = []
            
            revenue = proven_performance.get("avg_daily_revenue", 0.0)
            vector.append(min(revenue / 10000.0, 1.0))
            
            transaction_value = proven_performance.get("avg_transaction_value", 0.0)
            vector.append(min(transaction_value / 100.0, 1.0))
            
            transaction_freq = proven_performance.get("transaction_frequency", 0.0)
            vector.append(min(transaction_freq / 1000.0, 1.0))
            
            revenue_per_sqm = proven_performance.get("revenue_per_sqm", 0.0)
            vector.append(min(revenue_per_sqm / 100.0, 1.0))
            
            budget = financial_capacity.get("budget", 0.0)
            vector.append(min(budget / 100000.0, 1.0))
            
            max_rent = financial_capacity.get("max_affordable_rent", 0.0)
            vector.append(min(max_rent / 50000.0, 1.0))
            
            rent_ratio = financial_capacity.get("current_rent_to_income_ratio", 0.0)
            vector.append(min(rent_ratio / 0.5, 1.0))
            
            min_traffic = requirements.get("min_traffic_needed", 0.0)
            vector.append(min(min_traffic / 100000.0, 1.0))
            
            requires_kitchen = requirements.get("required_facilities", {}).get("kitchen", False)
            vector.append(1.0 if requires_kitchen else 0.0)
            
            requires_vent = requirements.get("required_facilities", {}).get("ventilation", False)
            vector.append(1.0 if requires_vent else 0.0)
            
            preferred_zones = requirements.get("preferred_zones", [])
            vector.append(min(len(preferred_zones) / 10.0, 1.0))
            
            staff = business_profile.get("staff_count", 0)
            vector.append(min(staff / 50.0, 1.0))
            
            operating_hours = business_profile.get("operating_hours_match", False)
            vector.append(1.0 if operating_hours else 0.0)
            
            interest = market_fit_signals.get("interest_from_mall_owners", 0)
            vector.append(min(interest / 10.0, 1.0))
            
            offers = market_fit_signals.get("offers_received", 0)
            vector.append(min(offers / 20.0, 1.0))
            
            negotiation = market_fit_signals.get("negotiation_stage_count", 0)
            vector.append(min(negotiation / 10.0, 1.0))
            
            total_locs = historical_track_record.get("total_locations", 0)
            vector.append(min(total_locs / 100.0, 1.0))
            
            successful_locs = historical_track_record.get("successful_locations", 0)
            success_rate = successful_locs / total_locs if total_locs > 0 else 0.0
            vector.append(success_rate)
            
            avg_duration = historical_track_record.get("avg_location_duration_months", 0.0)
            vector.append(min(avg_duration / 60.0, 1.0))
            
            return vector
            
        except Exception as e:
            api_logger.error(f"Error building brand vector: {str(e)}")
            return [0.0] * self.get_dimension()


class VectorNormalizer:
    def __init__(self, target_dimension: int):
        self.target_dimension = target_dimension
    
    def normalize(self, vector: List[float]) -> List[float]:
        if not vector:
            return [0.0] * self.target_dimension
        
        np_vector = np.array(vector)
        
        current_length = len(np_vector)
        
        if current_length < self.target_dimension:
            padding = np.zeros(self.target_dimension - current_length)
            np_vector = np.concatenate([np_vector, padding])
        elif current_length > self.target_dimension:
            np_vector = np_vector[:self.target_dimension]
        
        if np_vector.max() > np_vector.min():
            np_vector = (np_vector - np_vector.min()) / (np_vector.max() - np_vector.min())
        else:
            np_vector = np.zeros_like(np_vector)
        
        norm = np.linalg.norm(np_vector)
        if norm > 0:
            np_vector = np_vector / norm
        
        return np_vector.tolist()
