# Mall-Business Recommendation System

A comprehensive AI-powered recommendation system that matches shopping malls with suitable businesses based on demographics, traffic patterns, budget requirements, and natural language search capabilities.

## System Overview

This system provides intelligent mall-business matching through:
- **AI-Powered Search**: Natural language queries processed by Google Gemini API
- **Advanced Analytics**: Demographics and traffic pattern analysis
- **Recommendation Engine**: Multi-factor scoring algorithms
- **Real-time Performance**: Redis caching and Elasticsearch indexing

## Architecture

### Phase 1: Theoretical Design

#### Problem Framing
This is a matching problem where:
- **Malls (supply side)** have booths with attributes: size, location, price, visitor traffic, demographics, past business success
- **Businesses (demand side)** have needs: space requirement, budget, expected traffic, type of visitors, and prior performance
- **Goal**: Suggest best-fit matches (Business â†” Mall) with compatibility scores

#### Data Sources
**Mall Side:**
- Booth metadata: floor plan, size, price, availability
- Visitor traffic: aggregated counts and patterns
- Historical tenant success (revenue, duration)

**Business Side:**
- Requirements: budget, space, traffic capacity
- Past performance in other malls
- Industry type (F&B, retail, services)

**Shared:**
- Transaction logs (past 3â€“6 months)
- Onboarding history and performance data

### Phase 2: Current Implementation (Rule-based + AI Search)

**Data Sources:** Mall features (rent, traffic, demographics) + Business features (budget, target customers)

**Scoring Algorithm:**
- **Budget Fit** â†’ ratio (business budget / mall rent) â†’ normalized
- **Traffic Fit** â†’ cosine similarity between mall traffic vector & business traffic need
- **Demographic Fit** â†’ cosine similarity between mall demographics & business target demographics
- **Final Score** = weighted average of fits

**AI Integration:**
- Natural language query processing via Google Gemini API
- Intelligent criteria extraction and field mapping
- Elasticsearch query optimization for complex searches

### Phase 3: Future ML Enhancement

**Goal:** Use machine learning to learn optimal scoring functions from historical data

**Approach:**
1. **Feature Engineering** - Reuse Phase 2 features plus raw features (mall size, location embeddings, shop category)
2. **Label Collection** - Historical outcomes (accepted/rejected matches, revenue, rental duration)
3. **Model Training** - Logistic Regression, XGBoost/LightGBM, Neural Networks
4. **Prediction API** - ML-based probability scores and ranking

## Core Features

### AI-Powered Natural Language Search

The system processes natural language queries to search malls using Google Gemini API integration:

```python
# Example queries:
"find premium malls with elevator access"
"malls in District 1 under $500 management fee"
"shopping centers with parking spaces and high foot traffic"
```

**Search Pipeline:**
1. **Input Validation** - Security checks and sanitization
2. **AI Processing** - Gemini API extracts search criteria
3. **Query Building** - Convert to Elasticsearch DSL
4. **Results Formatting** - Return structured mall data

**Implementation Example:**
```python
async def search_malls_with_ai(self, query: str, limit: int = 10) -> Dict[str, Any]:
    # Validate input
    if not query or len(query.strip()) < 3:
        raise ValidationError("Query must be at least 3 characters")
    
    # Process with AI
    criteria = await self.ai_service.extract_search_criteria(query)
    
    # Build Elasticsearch query
    es_query = self._build_elasticsearch_query(criteria, limit)
    
    # Execute search
    response = await self.es_client.search(
        index="malls", 
        body=es_query
    )
    
    return self._format_search_results(response, query)
```

### Recommendation Algorithms

**Multi-Factor Scoring System:**
- Demographics compatibility analysis
- Traffic pattern matching
- Budget alignment calculations
- Historical performance weighting

**Caching Strategy:**
- Redis for demographic calculations
- Elasticsearch for search results
- Database connection pooling

### Data Models

**Core Entities:**
- `Mall`: Location, pricing, traffic, demographics
- `Business`: Requirements, budget, category, history
- `Booth`: Individual rental spaces within malls
- `BusinessHistory`: Performance tracking and success metrics

### API Architecture

**Search Endpoints:**
```bash
# AI-powered mall search
GET /search/malls?query="premium malls with parking"&limit=10

# Traditional recommendation endpoints
GET /recommendations?limit=10&use_cache=true
GET /recommendations/mall/{mall_id}
GET /recommendations/business/{business_id}
```

**Response Format:**
```json
{
  "success": true,
  "query": "premium malls with parking",
  "total_found": 15,
  "results": [
    {
      "mall_id": "uuid",
      "mall_name": "Premium Shopping Center",
      "mall_type": "Premium",
      "district": "District 1",
      "rent_price_usd": 1200,
      "management_fee_usd": 150,
      "avg_daily_visitors": 8000,
      "facilities": ["parking", "elevator", "escalator"],
      "score": 0.92
    }
  ]
}
```

## Technical Implementation

### AI Search Service

**Google Gemini Integration:**
```python
class AISearchService:
    async def extract_search_criteria(self, query: str) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": self._build_extraction_prompt(query)}]
            }]
        }
        
        response = await self.client.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        return self._parse_ai_response(response.json())
```

**Field Mapping:**
- `mall_name` â†’ Name/title searches
- `mall_type` â†’ Category filtering (Premium, Standard, Budget)
- `district` â†’ Geographic location
- `rent_price_usd` â†’ Budget range filtering
- `management_fee_usd` â†’ Additional cost considerations
- `avg_daily_visitors` â†’ Traffic volume requirements

### Elasticsearch Integration

**Query Generation:**
```python
def _build_elasticsearch_query(self, criteria: Dict, limit: int) -> Dict:
    query = {
        "query": {
            "bool": {
                "must": [],
                "should": [],
                "filter": []
            }
        },
        "size": limit,
        "sort": [{"_score": {"order": "desc"}}]
    }
    
    # Add criteria-based filters
    for field, value in criteria.items():
        if isinstance(value, list):
            # Multi-value fields (e.g., facilities)
            query["query"]["bool"]["should"].extend([
                {"match": {field: v}} for v in value
            ])
        elif isinstance(value, dict) and "range" in value:
            # Range queries (price, visitors)
            query["query"]["bool"]["filter"].append({
                "range": {field: value["range"]}
            })
        else:
            # Exact matches
            query["query"]["bool"]["must"].append({
                "match": {field: value}
            })
    
    return query
```

### Security Features

**Input Validation:**
- Query length limits (max 500 characters)
- SQL injection prevention
- Field validation against allowed schema
- Rate limiting and sanitization

**Error Handling:**
```python
# Custom exception hierarchy
from app.exception.custom_exceptions import AIProcessingError, GeminiAPIError
from app.exception.api_exceptions import ValidationError, NotFoundError
from app.exception.database_exceptions import QueryExecutionError
```

### Performance Optimization

**Caching Strategy:**
- Redis for frequently accessed demographic data
- Elasticsearch result caching
- Database query optimization with connection pooling

### Search Optimization
- ELK Stack version 8.15 for optimal performance
- Async HTTP clients for non-blocking operations
- Connection pooling for database operations

## Current System Architecture

### Core Components

1. **FastAPI Web Application** (`app/`)
   - REST API endpoints for recommendations and search
   - Authentication and authorization middleware
   - Request validation and error handling

2. **AI-Powered Search** (`app/config/elasticsearch.py`)
   - Natural language query processing using Gemini API
   - Intelligent criteria extraction and validation
   - Elasticsearch query optimization

3. **Recommendation Engine** (`app/service/`)
   - Demographics-based matching algorithms
   - Traffic pattern analysis
   - Budget compatibility scoring
   - Feature extraction and normalization

4. **Data Layer** (`app/model/`, `app/datastore/`)
   - PostgreSQL database with SQLAlchemy ORM
   - Redis caching for performance optimization
   - ETL processes for data ingestion

5. **Search Infrastructure**
   - Elasticsearch cluster for advanced search capabilities
   - Real-time indexing via Logstash
   - Kibana for search analytics and monitoring

### Technology Stack

**Backend Framework**
- FastAPI with Pydantic for API development
- Uvicorn ASGI server for production deployment
- Python 3.12+ with type hints

**AI & Search**
- Google Gemini API for natural language processing
- Elasticsearch 8.15 for search and analytics
- HTTPX for async HTTP client operations

**Data Storage**
- PostgreSQL for relational data
- Redis for caching and session management
- ELK Stack for search indexing and analytics

**Development & Deployment**
- Python virtual environments (.venv)
- Environment-based configuration (.env)
- Comprehensive exception handling system

## API Endpoints Summary

### Core Recommendation API
- `GET /recommendations` - Get top mall-business matches
- `GET /recommendations/mall/{mall_id}` - Business recommendations for specific mall
- `GET /recommendations/business/{business_id}` - Mall recommendations for specific business

### AI-Powered Search API
- `GET /search/malls` - Natural language mall search
- Query examples:
  - "find premium malls with elevator"
  - "malls in District 1 under $500 management fee"
  - "shopping centers with parking spaces"

### System Health & Cache Management
- `GET /health` - Service health status
- `POST /cache/demographics` - Calculate and cache demographics
- `GET /cache/status` - Cache system status

## Next Phase Roadmap

### Phase 4: Advanced ML Integration
- Collaborative filtering based on historical success data
- Content-based recommendations using mall-business similarity
- Hybrid recommendation models combining multiple approaches

### Phase 5: Real-Time Analytics
- Live traffic monitoring and analysis
- Dynamic pricing recommendations
- Performance dashboards and insights

### Phase 6: Market Intelligence
- Competitive analysis and market trends
- Predictive analytics for business success
- ROI optimization and forecasting

The current system provides a robust foundation for mall-business matching with AI-powered search capabilities, efficient caching, and scalable architecture ready for future ML enhancements.

5. **Search Infrastructure**
   - Elasticsearch cluster for advanced search capabilities
   - Real-time indexing via Logstash
   - Kibana for search analytics and monitoring

### Technology Stack

**Backend Framework**
- FastAPI with Pydantic for API development
- Uvicorn ASGI server for production deployment
- Python 3.12+ with type hints

**AI & Search**
- Google Gemini API for natural language processing
- Elasticsearch 8.15 for search and analytics
- HTTPX for async HTTP client operations

**Data Storage**
- PostgreSQL for relational data
- Redis for caching and session management
- ELK Stack for search indexing and analytics

**Development & Deployment**
- Python virtual environments (.venv)
- Environment-based configuration (.env)
- Comprehensive exception handling system

## API Endpoints Summary

### Core Recommendation API
- `GET /recommendations` - Get top mall-business matches
- `GET /recommendations/mall/{mall_id}` - Business recommendations for specific mall
- `GET /recommendations/business/{business_id}` - Mall recommendations for specific business

### AI-Powered Search API
- `GET /search/malls` - Natural language mall search
- Query examples:
  - "find premium malls with elevator"
  - "malls in District 1 under $500 management fee"
  - "shopping centers with parking spaces"

### System Health & Cache Management
- `GET /health` - Service health status
- `POST /cache/demographics` - Calculate and cache demographics
- `GET /cache/status` - Cache system status

## Next Phase Roadmap

### Phase 4: Advanced ML Integration
- Collaborative filtering based on historical success data
- Content-based recommendations using mall-business similarity
- Hybrid recommendation models combining multiple approaches

### Phase 5: Real-Time Analytics
- Live traffic monitoring and analysis
- Dynamic pricing recommendations
- Performance dashboards and insights

### Phase 6: Market Intelligence
- Competitive analysis and market trends
- Predictive analytics for business success
- ROI optimization and forecasting

The current system provides a robust foundation for mall-business matching with AI-powered search capabilities, efficient caching, and scalable architecture ready for future ML enhancements.
