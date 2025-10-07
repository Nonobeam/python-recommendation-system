import asyncio
import json
import os
import httpx
from typing import Any, Dict, List
from dotenv import load_dotenv
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
root_path = Path(__file__).parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")

# Create MCP server
server = Server("recommendation-gemini-server")

class GeminiAPIClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': api_key
        }
    
    async def generate_content(self, text: str, operation: str = "generateContent") -> Dict[str, Any]:
        """Generate content using Gemini API"""
        url = self.api_url.replace("generateContent", operation)
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "error": f"HTTP error: {str(e)}",
                    "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                }
            except Exception as e:
                return {
                    "error": f"Unexpected error: {str(e)}"
                }

# Initialize Gemini client
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = GeminiAPIClient(GEMINI_API_KEY, GEMINI_API_URL)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    tools = [
        Tool(
            name="gemini_generate_content",
            description="Generate content using Google Gemini API",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text prompt to send to Gemini"
                    },
                    "operation": {
                        "type": "string",
                        "description": "API operation to perform",
                        "default": "generateContent",
                        "enum": ["generateContent", "streamGenerateContent", "countTokens"]
                    }
                },
                "required": ["text"]
            }
        )
    ]
    
    if not GEMINI_API_KEY:
        tools = [tool for tool in tools if not tool.name.startswith("gemini_")]
        
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "gemini_generate_content":
        if not gemini_client:
            return [TextContent(
                type="text",
                text="Error: Gemini API key not configured. Please set GEMINI_API_KEY in environment variables."
            )]
        
        text = arguments.get("text", "")
        operation = arguments.get("operation", "generateContent")
        
        if not text:
            return [TextContent(
                type="text",
                text="Error: No text provided for content generation."
            )]
        
        result = await gemini_client.generate_content(text, operation)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Error: Unknown tool '{name}'"
        )]

async def main():
    """Main server entry point"""
    if GEMINI_API_KEY:
        print("Gemini API key configured")
    else:
        print("Gemini API key not found in environment. Set GEMINI_API_KEY to enable Gemini features.")
    
    print(f"Starting MCP server with URL: {GEMINI_API_URL}")
    print("Available tools: gemini_generate_content")
    
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            initialization_options={}
        )

if __name__ == "__main__":
    asyncio.run(main())