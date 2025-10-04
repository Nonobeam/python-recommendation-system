# Mall-Business Recommendation API

A REST API service for matching malls with businesses based on demographics, traffic patterns, and budget requirements.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your database and Redis configuration:
```env
DB_HOST=your_db_host
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_PORT=4003
DB_NAME=your_database
DB_SCHEMA=your_schema

REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_DEMOGRAPHIC_KEY_PREFIX=mall_demographic_
REDIS_CACHE_BUSINESS_KEY_PREFIX=mall_business_
```

### 3. Start the API Service
```bash
# Windows
start_api.bat

# Or manually
python server.py
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Get Top Recommendations
```
GET /recommendations?limit=10&use_cache=true
```
Returns top N mall-business matches sorted by compatibility score.

**Parameters:**
- `limit` (int): Number of recommendations (1-100, default: 10)
- `use_cache` (bool): Use cached data (default: true)

**Response:**
```json
{
    "success": true,
    "count": 10,
    "recommendations": [
        {
            "mall_id": "uuid",
            "business_id": "uuid",
            "budget_fit": 0.85,
            "traffic_fit": 0.72,
            "demo_fit": 0.91,
            "score": 0.83
        }
    ]
}
```

### Get Recommendations for Specific Mall
```
GET /recommendations/mall/{mall_id}?limit=10
```
Returns best business matches for a specific mall.

### Get Recommendations for Specific Business
```
GET /recommendations/business/{business_id}?limit=10
```
Returns best mall matches for a specific business.

### Cache Management
```
POST /cache/clear
GET /cache/status
```
Clear all cached data or check cache status.

## API Documentation

Once the service is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Architecture

```
app/
├── config/         # Database and Redis configuration
├── datastore/      # ETL and cache management
├── model/          # Database models
├── service/        # Business logic (feature extraction)
├── rest/           # FastAPI routes and endpoints
└── main.py         # Service entry point
```

## Scoring Algorithm

The recommendation score is calculated using:
- **Budget Fit (40%)**: How well business budget matches mall requirements
- **Traffic Fit (30%)**: Compatibility between mall traffic and business capacity
- **Demographic Fit (30%)**: Similarity between mall demographics and business target audience

## Caching

- **Demographic Data**: Cached per mall with Redis keys `mall_demographic_{mall_id}`
- **Recommendations**: Cached for 30 minutes to improve performance
- **ETL Data**: Individual caching strategy for optimal performance

## Performance Features

- Redis caching for fast data retrieval
- Configurable cache expiration
- Bulk recommendation processing
- Background data loading