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
POST /mcp/generate-content - Generate content using Gemini AI

##### Generate Content API Example
```bash
curl -X POST "http://localhost:8000/mcp/generate-content" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Explain how AI can help match businesses with mall locations",
    "operation": "generateContent",
    "max_output_tokens": 500,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 60
  }'
```

Request Parameters:
- `text` (required): Text prompt to send to Gemini
- `operation` (optional): API operation ("generateContent", "streamGenerateContent", "countTokens")
- `max_output_tokens` (optional): Maximum tokens to generate (1-8192, default: 2048)
- `temperature` (optional): Controls randomness (0.0-2.0, default: 1.0)
- `top_p` (optional): Nucleus sampling parameter (0.0-1.0, default: 0.95)
- `top_k` (optional): Top-k sampling parameter (1-100, default: 64)

Response format:
```json
{
  "success": true,
  "operation": "generateContent",
  "input_text": "Explain how AI can help match businesses with mall locations",
  "generation_config": {
    "max_output_tokens": 500,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 60
  },
  "result": {
    "candidates": [
      {
        "content": {
          "parts": [
            {
              "text": "AI-generated content here..."
            }
          ]
        }
      }
    ]
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

#### 1. gemini_generate_content
Generate content using Google Gemini API with configurable operations.

Parameters:
- text (required): Text prompt to send to Gemini
- operation (optional): API operation (generateContent, streamGenerateContent, countTokens)

#### 2. recommendation_analysis
Analyze business/mall compatibility using Gemini AI.

Parameters:
- mall_data (optional): Mall information for analysis
- business_data (optional): Business information for analysis
- analysis_type (required): compatibility, market_fit, risk_assessment, optimization_suggestions

#### 3. demographic_insights
Generate demographic insights and market analysis.

Parameters:
- demographic_data (required): Demographic data to analyze
- insight_type (required): trend_analysis, target_audience, market_opportunities, competitive_analysis

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