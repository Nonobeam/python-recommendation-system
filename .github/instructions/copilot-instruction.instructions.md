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
  config/ # Configuration files (e.g., db.py, redis.py)
  exception/ # Custom exceptions
  datastore/ # Data extraction and repository
  model/ # Database models
  service/ # Business logic and recommendation algorithms
  rest/ # REST API endpoints
  utils/ # Utility functions
  app.py            # Entry point of the application (renamed from server.py)
mcp-server/
  mcp_server.py     # MCP server for Gemini AI integration
  config.py         # Security and database configuration
  security.py       # SQL injection prevention and validation

# Code logging
Don't use icon/emoji in logging messages.

# Code commenting
Don't comment in any code lines. Only add comments in markdown files.

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

# Build an MCP client

## Overview
When building MCP clients for this project, follow the Python implementation guidelines since this is a Python-based recommendation system.

## System Requirements
- Python 3.8 or higher (already met in this project)
- Virtual environment (already configured as .venv)
- MCP Python SDK (already installed)
- Required dependencies in requirements.txt

## MCP Client Implementation Guidelines

### Basic Client Structure
Always create MCP clients following this pattern:

```python
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    
    async def connect_to_server(self, server_script_path: str):
        # Server connection logic
        pass
    
    async def process_query(self, query: str) -> str:
        # Query processing logic
        pass
    
    async def cleanup(self):
        # Resource cleanup
        await self.exit_stack.aclose()
```

### Server Connection Management
- Support both Python (.py) and JavaScript (.js) servers
- Use StdioServerParameters for server configuration
- Always validate server script extensions
- Implement proper error handling for connection failures

### Query Processing Logic
- Use async/await patterns consistently
- Handle tool calls through the MCP session
- Maintain conversation context when needed
- Process responses and format output appropriately

### Resource Management
- Always use AsyncExitStack for proper cleanup
- Close connections when done
- Handle server disconnections gracefully
- Implement timeout handling for long-running operations

### Integration with Existing System
When creating MCP clients for this recommendation system:

1. **Import Existing Modules**: Leverage existing database models and services
2. **Use Environment Configuration**: Read API keys and configuration from .env
3. **Follow Project Structure**: Place MCP clients in appropriate service directories
4. **Security First**: Apply the same security validation as the MCP server
5. **Error Handling**: Use existing exception classes from app/exception/

### Example Integration Pattern
```python
# For this project's structure
from app.config.db import get_db
from app.service.security import SecurityValidator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class RecommendationMCPClient:
    def __init__(self):
        self.session = None
        self.db = get_db()
        
    async def query_recommendations(self, message: str) -> Dict[str, Any]:
        # Validate input using existing security
        if not SecurityValidator.validate_query_message(message):
            raise ValueError("Invalid query message")
            
        # Process through MCP server
        result = await self.session.call_tool("query_mall_data", {"message": message})
        return result
```

### Best Practices for This Project

1. **Reuse Existing Infrastructure**
   - Use existing database connections
   - Leverage current security validation
   - Follow established error handling patterns

2. **Maintain Consistency**
   - Follow the same async patterns as existing services
   - Use consistent response formats
   - Apply the same logging standards (no emojis)

3. **Security Integration**
   - Always validate inputs using SecurityValidator
   - Apply the same SQL injection prevention
   - Use existing error response formats

4. **Performance Considerations**
   - Implement connection pooling when appropriate
   - Cache MCP responses when beneficial
   - Use existing Redis caching infrastructure

### Testing MCP Clients
- Create simple test scripts to verify connectivity
- Test with actual MCP servers, not just mocks
- Validate security features work correctly
- Ensure proper cleanup in all scenarios

This approach ensures MCP clients integrate seamlessly with the existing recommendation system while following MCP protocol standards.

# API Documentation
## Mall-Business Recommendation API

A REST API service for matching malls with businesses based on demographics, traffic patterns, and budget requirements.

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

#### MCP/Gemini AI Integration
GET /mcp/tools - Get list of available MCP tools
GET /mcp/tools/{tool_name} - Get details for a specific MCP tool
GET /mcp/status - Get MCP server status and configuration
POST /mcp/query-malls - Query mall database using natural language AI

##### Query Malls with AI API Example
```bash
curl -X POST "http://localhost:8000/mcp/query-malls" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find malls in District 1 with rent under $1000"
  }'
```

Request Parameters:
- `message` (required): Natural language query about malls

Response format:
```json
{
  "success": true,
  "query": "Find malls in District 1 with rent under $1000",
  "result": {
    "malls": [
      {
        "mall_id": "uuid",
        "name": "Mall Name",
        "district": "District 1",
        "rent_price_usd": 950,
        "address": "Full address",
        "management_fee_usd": 100,
        "avg_daily_visitors": 5000
      }
    ],
    "success": true,
    "total_found": 1
  }
}
```

### API Documentation URLs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

# MCP Server Documentation
## MCP Server for Recommendation System

The MCP (Model Context Protocol) server provides AI-powered tools for analyzing mall and business recommendations using Google's Gemini API.

### Environment Configuration

Required environment variables for MCP server:
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

### MCP Server Available Tools

#### 1. query_mall_data
Secure query mall database using natural language with AI-powered search criteria extraction and SQL injection prevention.

Parameters:
- message (required): Natural language query about malls (e.g., 'find malls in District 1 with rent under $1000')

Security Features:
- SQL injection prevention with parameterized queries
- Input validation and sanitization
- Blocked keyword detection
- Field validation against allowed database schema
- Maximum query length limits
- Response data sanitization

The tool uses Google Gemini API to:
1. Extract search criteria from natural language input
2. Validate and sanitize all inputs for security
3. Map criteria to allowed database fields: name, type, avg_daily_visitors, rent_price_usd, management_fee_usd, vat_percent, motorbike_fee_vnd, car_fee_vnd, electricity_policy, overtime_fee_policy, lease_term, deposit_policy, payment_policy, address, city, district
4. Build secure parameterized SQL queries
5. Execute queries with additional syntax validation
6. Return sanitized mall data with success indicators

### API URL Configuration
The GEMINI_API_URL supports different operations:
- generateContent - Generate text content (default)
- streamGenerateContent - Stream content generation  
- countTokens - Count tokens in input

### Security Notes
- Never commit your actual API key to version control
- Keep your .env file in .gitignore
- Rotate your API keys regularly
- Monitor your API usage and costs
- All database queries use parameterized statements to prevent SQL injection
- Input validation prevents malicious content from reaching the database
- Response sanitization ensures only safe data is returned to users

### Security Configuration
The MCP server includes comprehensive security layers:

#### Input Validation (`mcp-server/security.py`)
- Message length limits (max 1000 characters)
- Blocked SQL keywords detection
- Character validation using regex patterns
- Numeric value range validation
- Maximum criteria count limits

#### Query Builder (`mcp-server/security.py`)
- Parameterized SQL queries only
- Field validation against allowed schema
- Query syntax validation
- Automatic result limiting (max 100 rows)

#### Configuration (`mcp-server/config.py`)
- Centralized security settings
- Database field definitions with validation rules
- Gemini API configuration
- Type validation and constraints

### Starting the MCP Server
Run the MCP server using Python directly:
```bash
python mcp-server/mcp_server.py
```

### MCP Server Integration
The MCP server complements the existing FastAPI recommendation system by providing:
- AI-powered analysis of recommendation results
- Natural language insights for demographic data
- Market fit assessments for business-mall pairings
- Optimization suggestions based on AI analysis