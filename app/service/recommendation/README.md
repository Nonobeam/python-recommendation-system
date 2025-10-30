# Demographics-Based Recommendation System

## Overview

This recommendation system calculates compatibility scores between brands and malls using demographic data. The architecture follows SOLID principles with clear separation of concerns across data retrieval, vector construction, score calculation, and service orchestration.

## Architecture

### Layer 1: Data Retrieval (`repositories.py`)

**Components**:
- `DemographicRepository`: Abstract interface for data access
- `RedisDemographicRepository`: Redis cache operations
- `PostgresDemographicRepository`: PostgreSQL database queries
- `DemographicDataSource`: Cache-first data retrieval orchestrator

**Features**:
- Cache-first strategy with Redis fallback to PostgreSQL
- Automatic cache population on miss
- Cache statistics tracking
- Default TTL: 3600 seconds

### Layer 2: Vector Construction (`vector_builders.py`)

**Components**:
- `VectorBuilder`: Interface for vector construction
- `MallVectorBuilder`: Transforms mall demographics into 14-dimensional vectors
- `BrandVectorBuilder`: Transforms brand demographics into 19-dimensional vectors
- `VectorNormalizer`: Normalizes vectors to consistent length and scale

**Mall Vector Features**:
- Tenant mix ratios (shop_percent, food_percent, service_percent)
- Zone performance metrics
- Historical performance indicators
- Market intelligence data
- Verification status

**Brand Vector Features**:
- Proven performance metrics
- Financial capacity indicators
- Business requirements
- Market fit signals
- Historical track record

### Layer 3: Score Calculation (`score_calculators.py`)

**Components**:
- `DemographicScoreCalculator`: Cosine similarity between vectors
- `BudgetCompatibilityCalculator`: Budget range evaluation
- `TrafficCompatibilityCalculator`: Traffic pattern matching
- `HistoricalPerformanceCalculator`: Success history analysis
- `TenantMixCompatibilityCalculator`: Category saturation checking
- `WeightedScoreAggregator`: Combines scores with configurable weights

**Score Components**:
1. **Demographic Similarity** (25%): Vector similarity using cosine distance
2. **Budget Compatibility** (20%): Brand budget vs mall pricing
3. **Traffic Compatibility** (20%): Visitor volume matching
4. **Historical Performance** (20%): Past success indicators
5. **Tenant Mix** (15%): Category availability

### Layer 4: Service Layer (`services.py`)

**Components**:
- `SingleMatchService`: Single brand-mall pair scoring
- `BatchMatchService`: Multiple mall evaluation for one brand
- `CacheInvalidationService`: Cache management on data updates

## API Endpoints

### POST `/pri/api/v1/recommendations/score`

Calculate compatibility score for a single brand-mall pair.

**Request**:
```json
{
  "brand_id": "550e8400-e29b-41d4-a716-446655440000",
  "mall_id": "660e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "success": true,
  "result": {
    "brand_id": "...",
    "mall_id": "...",
    "final_score": 0.8245,
    "component_scores": {
      "demographic": 0.85,
      "budget": 0.90,
      "traffic": 0.80,
      "historical": 0.75,
      "tenant_mix": 0.85
    },
    "explanations": {
      "demographic": "Excellent demographic match...",
      "budget": "Budget alignment is strong...",
      "traffic": "Traffic patterns align well...",
      "historical": "Strong historical performance...",
      "tenant_mix": "Good tenant mix fit..."
    },
    "calculation_timestamp": "2024-10-21T10:00:00",
    "market_interest_boost_applied": true
  },
  "calculation_time_ms": 45.23
}
```

### POST `/pri/api/v1/recommendations/batch-score`

Calculate scores for multiple malls.

**Request**:
```json
{
  "brand_id": "550e8400-e29b-41d4-a716-446655440000",
  "mall_ids": [
    "660e8400-e29b-41d4-a716-446655440000",
    "770e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response**:
```json
{
  "success": true,
  "brand_id": "...",
  "total_evaluated": 2,
  "results": [
    {
      "mall_id": "...",
      "final_score": 0.8245,
      "component_scores": {...},
      "explanations": {...}
    }
  ]
}
```

### GET `/pri/api/v1/recommendations/metrics`

Get system performance metrics.

**Response**:
```json
{
  "success": true,
  "metrics": {
    "cache": {
      "hits": 1250,
      "misses": 340,
      "hit_rate": 0.786
    },
    "calculations": {
      "count": 1590,
      "average_time_ms": 42.15,
      "min_time_ms": 18.32,
      "max_time_ms": 156.78
    },
    "score_distribution": {
      "excellent": 420,
      "good": 680,
      "moderate": 350,
      "poor": 140,
      "total": 1590
    },
    "errors": 12,
    "uptime_seconds": 86400.0
  }
}
```

## Configuration

### Score Weights

Default weights (configurable in `recommendation_config.py`):
- Demographic: 25%
- Budget: 20%
- Traffic: 20%
- Historical: 20%
- Tenant Mix: 15%

### Cache Configuration

- Brand demographics TTL: 3600 seconds
- Mall demographics TTL: 3600 seconds
- Recommendation cache TTL: 1800 seconds

## Usage Example

```python
from app.service.recommendation.services import SingleMatchService

# Initialize service
service = SingleMatchService()

# Calculate match score
result = service.calculate_match_score(
    brand_id="550e8400-e29b-41d4-a716-446655440000",
    mall_id="660e8400-e29b-41d4-a716-446655440000"
)

print(f"Final Score: {result['final_score']}")
print(f"Budget Score: {result['component_scores']['budget']}")
```

## Error Handling

The system raises specific exceptions:

- `DemographicsError`: When demographic data is missing
- `ScoreCalculationError`: When calculation fails
- `ValidationError`: When input validation fails

All errors are logged and tracked in metrics.

## Performance Optimization

1. **Caching**: Redis cache reduces database load by 70%+
2. **Batch Processing**: Brand vector built once and reused
3. **Parallel Processing**: Future enhancement for multiple malls
4. **Vector Reuse**: Normalized vectors cached within request

## Testing

Unit tests should cover:
- Each vector builder with various inputs
- Each calculator with edge cases
- Normalizer with different vector lengths
- Aggregator with various weight combinations

Integration tests should verify:
- Data retrieval from cache and database
- End-to-end API flows
- Cache population and invalidation

## Monitoring

The system tracks:
- Cache hit/miss rates
- Calculation execution times
- Score distributions
- Error counts
- System uptime

Access metrics via the `/recommendations/metrics` endpoint.
