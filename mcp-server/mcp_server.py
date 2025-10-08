import asyncio
import json
import os
import httpx
import sys
from typing import Any, Dict, List
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Security and configuration imports
from config import GeminiConfig, DatabaseConfig, get_allowed_fields_description
from ..app.security import SecurityValidator, QueryBuilder, ResponseSanitizer

# Load environment variables
root_path = Path(__file__).parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

# Database configuration
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_SCHEMA = os.getenv("DB_SCHEMA")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?options=-c%20search_path%3D{DB_SCHEMA}"
)

# Gemini API configuration
GEMINI_API_KEY = GeminiConfig.API_KEY
GEMINI_API_URL = GeminiConfig.API_URL

# Create database engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Import models
from app.model.models import Mall

# Create MCP server
server = Server("recommendation-mall-query-server")

class GeminiAPIClient:
    """Secure client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': api_key
        }
    
    async def extract_query_intent(self, user_message: str) -> Dict[str, Any]:
        """Use Gemini to extract database query intent from user message with security validation"""
        
        # Security validation first
        if not SecurityValidator.validate_query_message(user_message):
            raise ValueError("Invalid or potentially unsafe query message")
        
        # Create secure prompt with allowed fields
        allowed_fields = get_allowed_fields_description()
        
        prompt = GeminiConfig.QUERY_EXTRACTION_PROMPT.format(
            allowed_fields=allowed_fields,
            user_message=user_message
        )
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": GeminiConfig.QUERY_EXTRACTION_CONFIG
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=GeminiConfig.API_TIMEOUT
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract JSON from response
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0].get("content", {})
                    if "parts" in content and content["parts"]:
                        text_response = content["parts"][0].get("text", "{}")
                        
                        # Parse and validate extracted criteria
                        try:
                            raw_criteria = json.loads(text_response.strip())
                            # Validate and sanitize the extracted criteria
                            validated_criteria = SecurityValidator.validate_extracted_criteria(raw_criteria)
                            return validated_criteria
                        except json.JSONDecodeError:
                            return {}
                
                return {}
                
        except Exception as e:
            raise Exception(f"Failed to extract query intent: {str(e)}")

async def query_malls_from_db(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Secure query malls from database using parameterized queries"""
    
    try:
        # Validate and sanitize query parameters
        validated_params = SecurityValidator.validate_extracted_criteria(query_params)
        
        if not validated_params:
            return ResponseSanitizer.create_success_response([], 0)
        
        # Build secure SQL query
        sql_query, parameters = QueryBuilder.build_mall_query(validated_params)
        
        # Additional query validation
        if not QueryBuilder.validate_query_syntax(sql_query):
            return ResponseSanitizer.create_error_response("Invalid query syntax", "security_error")
        
        # Execute query safely
        with SessionLocal() as session:
            result = session.execute(text(sql_query), parameters)
            rows = result.fetchall()
            
            # Convert to dictionaries
            columns = result.keys()
            mall_data = [dict(zip(columns, row)) for row in rows]
            
            # Sanitize response data
            sanitized_data = ResponseSanitizer.sanitize_mall_data(mall_data)
            
            return ResponseSanitizer.create_success_response(sanitized_data, len(sanitized_data))
            
    except Exception as e:
        return ResponseSanitizer.create_error_response(f"Database query failed: {str(e)}", "database_error")

# Initialize Gemini client
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = GeminiAPIClient(GEMINI_API_KEY, GEMINI_API_URL)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    tools = [
        Tool(
            name="query_mall_data",
            description="Secure query mall database using natural language with AI-powered extraction and SQL injection prevention.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Natural language query about malls (e.g., 'find malls in District 1 with rent under $1000')"
                    }
                },
                "required": ["message"]
            }
        )
    ]
    
    if not GEMINI_API_KEY:
        return []
        
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "query_mall_data":
        if not gemini_client:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Gemini API key not configured. Please set GEMINI_API_KEY in environment variables.",
                    "success": False
                }, indent=2)
            )]
        
        message = arguments.get("message", "")
        
        if not message.strip():
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "No message provided for mall query.",
                    "success": False
                }, indent=2)
            )]
        
        try:
            # Step 1: Use Gemini to extract query intent
            query_params = await gemini_client.extract_query_intent(message)
            
            # Step 2: Query database
            result = await query_malls_from_db(query_params)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Error processing mall query: {str(e)}",
                    "success": False
                }, indent=2)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Unknown tool '{name}'",
                "success": False
            }, indent=2)
        )]

async def main():
    """Main server entry point"""
    if GEMINI_API_KEY:
        print("Gemini API key configured")
    else:
        print("Gemini API key not found in environment. Set GEMINI_API_KEY to enable features.")
    
    print(f"Starting MCP server with database integration")
    print("Available tools: query_mall_data")
    
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            initialization_options={}
        )

if __name__ == "__main__":
    asyncio.run(main())