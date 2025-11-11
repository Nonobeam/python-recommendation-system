from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class CalculationMetrics:
    count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0

    def average_time_ms(self) -> float:
        return self.total_time_ms / self.count if self.count > 0 else 0.0


@dataclass
class ScoreDistributionMetrics:
    excellent_count: int = 0
    good_count: int = 0
    moderate_count: int = 0
    poor_count: int = 0

    def total(self) -> int:
        return self.excellent_count + self.good_count + self.moderate_count + self.poor_count


class RecommendationMetrics:
    def __init__(self):
        self.cache_metrics = CacheMetrics()
        self.calculation_metrics = CalculationMetrics()
        self.score_distribution = ScoreDistributionMetrics()
        self.error_count = 0
        self.start_time = datetime.now()

    def record_cache_hit(self):
        self.cache_metrics.hits += 1

    def record_cache_miss(self):
        self.cache_metrics.misses += 1

    def record_calculation(self, time_ms: float):
        self.calculation_metrics.count += 1
        self.calculation_metrics.total_time_ms += time_ms
        if time_ms < self.calculation_metrics.min_time_ms:
            self.calculation_metrics.min_time_ms = time_ms
        if time_ms > self.calculation_metrics.max_time_ms:
            self.calculation_metrics.max_time_ms = time_ms

    def record_score(self, score: float):
        if score >= 0.8:
            self.score_distribution.excellent_count += 1
        elif score >= 0.6:
            self.score_distribution.good_count += 1
        elif score >= 0.4:
            self.score_distribution.moderate_count += 1
        else:
            self.score_distribution.poor_count += 1

    def record_error(self):
        self.error_count += 1

    def get_summary(self) -> Dict:
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            "cache": {
                "hits": self.cache_metrics.hits,
                "misses": self.cache_metrics.misses,
                "hit_rate": round(self.cache_metrics.hit_rate(), 3),
            },
            "calculations": {
                "count": self.calculation_metrics.count,
                "average_time_ms": round(self.calculation_metrics.average_time_ms(), 2),
                "min_time_ms": (
                    round(self.calculation_metrics.min_time_ms, 2)
                    if self.calculation_metrics.min_time_ms != float("inf")
                    else 0
                ),
                "max_time_ms": round(self.calculation_metrics.max_time_ms, 2),
            },
            "score_distribution": {
                "excellent": self.score_distribution.excellent_count,
                "good": self.score_distribution.good_count,
                "moderate": self.score_distribution.moderate_count,
                "poor": self.score_distribution.poor_count,
                "total": self.score_distribution.total(),
            },
            "errors": self.error_count,
            "uptime_seconds": round(uptime_seconds, 2),
        }


GLOBAL_METRICS = RecommendationMetrics()
