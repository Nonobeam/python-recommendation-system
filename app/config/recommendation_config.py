from typing import Dict
from pydantic import BaseModel
from app.utils.logger import api_logger


class ScoreWeights(BaseModel):
    demographic: float = 0.25
    budget: float = 0.20
    traffic: float = 0.20
    historical: float = 0.20
    tenant_mix: float = 0.15
    
    def dict(self) -> Dict[str, float]:
        return {
            "demographic": self.demographic,
            "budget": self.budget,
            "traffic": self.traffic,
            "historical": self.historical,
            "tenant_mix": self.tenant_mix
        }
    
    def validate(self) -> bool:
        total = sum([self.demographic, self.budget, self.traffic, self.historical, self.tenant_mix])
        if abs(total - 1.0) > 0.01:
            api_logger.warning(f"Score weights sum to {total}, not 1.0")
            return False
        return True
    
    def normalize(self):
        total = sum([self.demographic, self.budget, self.traffic, self.historical, self.tenant_mix])
        if total > 0:
            self.demographic = self.demographic / total
            self.budget = self.budget / total
            self.traffic = self.traffic / total
            self.historical = self.historical / total
            self.tenant_mix = self.tenant_mix / total


class CacheConfig(BaseModel):
    brand_demographics_ttl: int = 3600
    mall_demographics_ttl: int = 3600
    recommendation_cache_ttl: int = 1800
    enable_cache: bool = True


class VectorConfig(BaseModel):
    target_dimension: int = 14
    normalization_enabled: bool = True
    max_vector_length: int = 50


class RecommendationConfig:
    def __init__(
        self,
        score_weights: ScoreWeights = None,
        cache_config: CacheConfig = None,
        vector_config: VectorConfig = None
    ):
        self.score_weights = score_weights or ScoreWeights()
        self.cache_config = cache_config or CacheConfig()
        self.vector_config = vector_config or VectorConfig()
        
        if not self.score_weights.validate():
            api_logger.warning("Normalizing score weights")
            self.score_weights.normalize()
    
    def update_score_weights(self, weights: Dict[str, float]):
        for key, value in weights.items():
            if hasattr(self.score_weights, key):
                setattr(self.score_weights, key, value)
        
        self.score_weights.normalize()
        api_logger.info(f"Updated score weights to: {self.score_weights.dict()}")


DEFAULT_CONFIG = RecommendationConfig()
