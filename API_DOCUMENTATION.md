# Mall-Business Recommendation API Documentation

## Overview

The Mall-Business Recommendation API provides comprehensive search and analytics capabilities for matching malls with businesses using AI-powered natural language processing and Elasticsearch.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Authentication

This API uses JWT (JSON Web Tokens) for authentication. Protected endpoints (those starting with `/pri`) require a valid JWT token in the Authorization header.

### Token Format
```
Authorization: Bearer <your-jwt-token>
```

### Required Token Claims
- `sub`: User ID (required)
- `brand_id`: Brand identifier for search history tracking
- `role`: User role/permissions
- `email`: User email address

## API Structure

### Public Endpoints (`/pub/*`)
- No authentication required
- Basic service information
- Health checks

### Private Endpoints (`/pri/*`) 
- JWT authentication required
- Business logic and search functionality
- Automatic search history logging

## Core Features

### 1. AI-Powered Search
```bash
GET /pri/api/v1/search/malls?q=premium malls with parking&page=1&size=10
```

**Natural Language Examples:**
- "Find premium malls with parking in District 1"
- "Malls under $500 management fee with elevator access"
- "Shopping centers with high foot traffic near metro stations"

### 2. Search History Tracking
Every search is automatically logged with:
- Brand ID from JWT token
- Complete search query text
- Timestamp of search
- User information

### 3. Pagination Support
All search endpoints support pagination:
- `page`: Page number (starts from 1)
- `size`: Results per page (1-100)

## Example Usage

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. AI-Powered Mall Search
```bash
curl -X GET \
  "http://localhost:8000/pri/api/v1/search/malls?q=premium%20malls%20with%20parking&page=1&size=10" \
  -H "Authorization: Bearer your-jwt-token"
```

### 3. Get Search History
```bash
curl -X GET \
  "http://localhost:8000/pri/api/v1/search/history?limit=50" \
  -H "Authorization: Bearer your-jwt-token"
```

## Response Format

### Success Response
```json
{
  "success": true,
  "user_id": "user_12345",
  "brand_id": "brand_67890",
  "original_query": "premium malls with parking",
  "extracted_criteria": {
    "mall_type": "Premium",
    "facilities": ["parking"]
  },
  "pagination": {
    "current_page": 1,
    "page_size": 10,
    "total_results": 25,
    "total_pages": 3,
    "has_more": true
  },
  "results": [
    {
      "mall_id": "mall_123",
      "mall_name": "Premium Shopping Center",
      "mall_type": "Premium",
      "district": "District 1",
      "rent_price_usd": 1200.0,
      "management_fee_usd": 150.0,
      "avg_daily_visitors": 8000,
      "facilities": ["parking", "elevator"],
      "score": 0.95
    }
  ]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Authentication required",
  "detail": "Invalid or expired JWT token"
}
```

## Search Criteria

The AI system can extract and use the following criteria:

- **mall_type**: Premium, Standard, Budget
- **district**: Geographic location
- **rent_price_usd**: Rental price range
- **management_fee_usd**: Management fee range
- **avg_daily_visitors**: Visitor traffic requirements
- **facilities**: Required amenities (parking, elevator, escalator, etc.)

## Status Codes

- `200 OK`: Successful request
- `401 Unauthorized`: Authentication required or invalid token
- `400 Bad Request`: Invalid parameters or missing required data
- `503 Service Unavailable`: External service (Elasticsearch) unavailable
- `500 Internal Server Error`: Unexpected server error

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended for production use.

## Support

For API support, please contact:
- **Email**: support@yourdomain.com
- **Documentation Issues**: Create an issue in the project repository

## Changes and Versioning

This API follows semantic versioning. Current version: `1.0.0`

### Version 1.0.0
- Initial release
- AI-powered mall search
- JWT authentication
- Brand search history tracking
- Comprehensive OpenAPI documentation