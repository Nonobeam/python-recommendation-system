"""
Service for interacting with MCP server tools
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")

class MCPToolService:
    """Service for managing MCP tools"""
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        tools = [
            {
                "name": "gemini_generate_content",
                "description": "Generate content using Google Gemini API",
                "status": "available" if GEMINI_API_KEY else "requires_api_key",
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
                    }
                }
            },
            {
                "name": "recommendation_analysis",
                "description": "Analyze business/mall recommendations using Gemini AI",
                "status": "available" if GEMINI_API_KEY else "requires_api_key",
                "parameters": {
                    "mall_data": {
                        "type": "object",
                        "required": False,
                        "description": "Mall information for analysis"
                    },
                    "business_data": {
                        "type": "object",
                        "required": False,
                        "description": "Business information for analysis"
                    },
                    "analysis_type": {
                        "type": "string",
                        "required": True,
                        "options": ["compatibility", "market_fit", "risk_assessment", "optimization_suggestions"],
                        "description": "Type of analysis to perform"
                    }
                }
            },
            {
                "name": "demographic_insights",
                "description": "Generate demographic insights using Gemini AI",
                "status": "available" if GEMINI_API_KEY else "requires_api_key",
                "parameters": {
                    "demographic_data": {
                        "type": "object",
                        "required": True,
                        "description": "Demographic data to analyze"
                    },
                    "insight_type": {
                        "type": "string",
                        "required": True,
                        "options": ["trend_analysis", "target_audience", "market_opportunities", "competitive_analysis"],
                        "description": "Type of insights to generate"
                    }
                }
            }
        ]
        
        # Filter tools based on API key availability
        if not GEMINI_API_KEY:
            # Mark all tools as requiring API key
            for tool in tools:
                tool["status"] = "requires_api_key"
                tool["note"] = "Set GEMINI_API_KEY environment variable to enable this tool"
        
        return tools
    
    @staticmethod
    def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
        """Get specific tool information by name"""
        tools = MCPToolService.get_available_tools()
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        return None
    
    @staticmethod
    def get_server_status() -> Dict[str, Any]:
        """Get MCP server status information"""
        return {
            "mcp_server": {
                "name": "recommendation-gemini-server",
                "url": GEMINI_API_URL,
                "gemini_api_configured": bool(GEMINI_API_KEY),
                "tools_count": len(MCPToolService.get_available_tools()),
                "status": "ready" if GEMINI_API_KEY else "configuration_required"
            }
        }