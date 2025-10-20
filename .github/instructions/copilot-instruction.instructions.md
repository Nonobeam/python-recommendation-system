---
applyTo: '**'
---
---
applyTo: '**'
---
# IGNORE FILE
This file is ignored by Copilot and Copilot should not read or suggest code based on its contents:
.env

# Project Instructions
Use this file to provide instructions for the project.
These instructions will be used by Copilot to understand the project context and provide better suggestions.

Always run the code in venv again after change some code.

# Code base structure
app/
  config/ # Configuration files (e.g., db.py, redis.py, elasticsearch.py)
  exception/ # Custom exceptions organized by type
    cache_exceptions.py      # Cache and Redis related exceptions
    custom_exceptions.py     # AI and Elasticsearch related exceptions
    api_exceptions.py        # REST API related exceptions
    database_exceptions.py   # Database operation exceptions
    recommendation_exceptions.py # Recommendation algorithm exceptions
  datastore/ # Data extraction and repository
  model/ # Database models
  service/ # Business logic and recommendation algorithms
  rest/ # REST API endpoints
  utils/ # Utility functions
  app.py            # Entry point of the application

# Exception Handling Guidelines
Always use appropriate exceptions from the exception module:
- Use cache_exceptions for Redis and caching operations
- Use custom_exceptions for AI processing and Elasticsearch operations
- Use api_exceptions for REST API validation and HTTP errors
- Use database_exceptions for database operations and model validation
- Use recommendation_exceptions for recommendation algorithm errors

When importing exceptions, use specific imports:
```python
from ..exception.custom_exceptions import AIProcessingError, GeminiAPIError
from ..exception.api_exceptions import ValidationError, NotFoundError
from ..exception.database_exceptions import QueryExecutionError, DatabaseConnectionError
```

# Code logging and printing
Don't use icon/emoji in logging messages or print statements.
Use clean, professional text only for all console output.
Examples:
- Good: "AI Search Service Connected: elasticsearch"
- Bad: "🔗 AI Search Service Connected: elasticsearch"
- Good: "Notified API server of search initialization"
- Bad: "✅ Notified API server of search initialization"

# Communication style
Don't use icons/emojis in any responses or communication.
Use clean, professional text only when explaining concepts, providing status updates, or describing solutions.
Keep responses focused and direct without visual decorations.

# Code commenting
Don't comment in any code lines. Only add comments in markdown files.

# Search infrastructure
Use ELK Stack version 8.15 for search infrastructure.
When implementing Logstash, Kibana, or Elasticsearch, always use version 8.15.
Ensure compatibility and consistency across all search components.
Logstash automatically syncs data from PostgreSQL database - no manual data synchronization needed.

# File creation restrictions
NEVER create .bat or .ps1 (PowerShell) files. Use Python scripts only.

# Run source code
Always run in venv and check before run if we are in venv or not.
Use this command to move into venv stage ".\venv\Scripts\Activate".

# Install dependencies
Always use pip to install dependencies.
Use this command to install dependencies "pip install -r requirements.txt".
Use this command to install a specific package "pip install package-name".
Use this command to install a specific package with version "pip install package-name==version".
Remember to always add the package to requirements.txt file.

# API Documentation
## Mall-Business Recommendation API

A REST API service for matching malls with businesses based on demographics, traffic patterns, and budget requirements with AI-powered natural language search.

### API Endpoints

#### Health Check
GET /health - Returns service health status.

#### Get Top Recommendations  
GET /recommendations?limit=10&use_cache=true
Returns top N mall-business matches sorted by compatibility score.

Parameters:
- limit (int): Number of recommendations (1-100, default: 10)
- use_cache (bool): Use cached data (default: true)

Response format:
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

#### Get Recommendations for Specific Mall
GET /recommendations/mall/{mall_id}?limit=10
Returns best business matches for a specific mall.

#### Get Recommendations for Specific Business  
GET /recommendations/business/{business_id}?limit=10
Returns best mall matches for a specific business.

#### Cache Management
POST /cache/demographics - Calculate and cache all demographics
GET /cache/status - Check cache status

#### AI-Powered Search
GET /search/malls - Search malls using natural language queries

##### AI Mall Search API Example
```bash
curl -X GET "http://localhost:8000/search/malls?query=find%20premium%20malls%20with%20parking&limit=10"
```

Request Parameters:
- `query` (required): Natural language query about malls
- `limit` (optional): Number of results (default: 10)

Response format:
```json
{
  "success": true,
  "query": "find premium malls with parking",
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
      "facilities": ["parking", "elevator"],
      "score": 0.92
    }
  ]
}
```

### API Documentation URLs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

# AI & Search Infrastructure
## AI-Powered Search System

The system provides natural language search capabilities using Google Gemini API for intelligent query processing and Elasticsearch for fast, scalable search operations.

### Environment Configuration

Required environment variables for AI search:
```bash
# Gemini API Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
```

### Getting a Gemini API Key
1. Go to Google AI Studio (https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key or use an existing one
5. Copy the API key and add it to your .env file

### AI Search Features

#### Natural Language Processing
Process user queries like:
- "find premium malls with elevator access"
- "malls in District 1 under $500 management fee"  
- "shopping centers with parking spaces and high foot traffic"

#### Security Features
- Input validation and sanitization
- Query length limits (max 500 characters)
- Field validation against allowed schema
- Rate limiting protection
- SQL injection prevention (even though using Elasticsearch)

#### Search Pipeline
1. **Input Validation** - Security checks and sanitization
2. **AI Processing** - Gemini API extracts search criteria from natural language
3. **Query Building** - Convert criteria to Elasticsearch DSL queries
4. **Results Formatting** - Return structured mall data with relevance scoring

### Field Mapping
The AI system maps natural language to these database fields:
- `mall_name` → Name/title searches
- `mall_type` → Category filtering (Premium, Standard, Budget)
- `district` → Geographic location
- `rent_price_usd` → Budget range filtering
- `management_fee_usd` → Additional cost considerations
- `avg_daily_visitors` → Traffic volume requirements

### Security Notes
- Never commit your actual API key to version control
- Keep your .env file in .gitignore
- Rotate your API keys regularly
- Monitor your API usage and costs
- All queries include proper validation and sanitization
- Input length limits prevent abuse
- Response sanitization ensures only safe data is returned