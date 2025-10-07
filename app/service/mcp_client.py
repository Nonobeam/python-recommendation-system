"""
MCP Integration for communicating with Gemini API
Simplified version that directly uses the MCP server logic
"""
import asyncio
import json
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

class SimpleMCPManager:
    """Simplified MCP manager that directly uses Gemini API logic"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
        
    async def generate_content(self, text: str, operation: str = "generateContent", 
                             max_output_tokens: int = 2048, temperature: float = 1.0,
                             top_p: float = 0.95, top_k: int = 64) -> Dict[str, Any]:
        """Generate content using Gemini API with configurable parameters"""
        if not self.api_key:
            raise Exception("Gemini API key not configured. Please set GEMINI_API_KEY in environment variables.")
        
        if not text.strip():
            raise Exception("No text provided for content generation.")
        
        try:
            import httpx
            
            # Replace operation in URL if needed
            url = self.api_url.replace("generateContent", operation)
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": max_output_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                    "topK": top_k
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")
    
    async def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools"""
        tools = [
            {
                "name": "gemini_generate_content",
                "description": "Generate content using Google Gemini API with configurable parameters",
                "status": "available" if self.api_key else "requires_api_key",
                "parameters": {
                    "text": {
                        "type": "string",
                        "required": True,
                        "description": "Text prompt to send to Gemini"
                    },
                    "operation": {
                        "type": "string",
                        "required": False,
                        "default": "generateContent",
                        "options": ["generateContent", "streamGenerateContent", "countTokens"],
                        "description": "API operation to perform"
                    },
                    "max_output_tokens": {
                        "type": "integer",
                        "required": False,
                        "default": 2048,
                        "min": 1,
                        "max": 8192,
                        "description": "Maximum number of tokens to generate"
                    },
                    "temperature": {
                        "type": "number",
                        "required": False,
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                        "description": "Controls randomness of output (0.0 = deterministic, 2.0 = very creative)"
                    },
                    "top_p": {
                        "type": "number",
                        "required": False,
                        "default": 0.95,
                        "min": 0.0,
                        "max": 1.0,
                        "description": "Nucleus sampling parameter"
                    },
                    "top_k": {
                        "type": "integer",
                        "required": False,
                        "default": 64,
                        "min": 1,
                        "max": 100,
                        "description": "Top-k sampling parameter"
                    }
                }
            }
        ]
        
        return {
            "tools": tools,
            "count": len(tools)
        }
    
    async def close(self):
        """Clean up resources (no-op for simplified version)"""
        pass

# Global MCP manager instance
mcp_manager = SimpleMCPManager()