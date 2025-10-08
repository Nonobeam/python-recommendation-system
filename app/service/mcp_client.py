import asyncio
import json
import os
import subprocess
import sys
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

class MCPServerManager:
    """Manager for communicating with the actual MCP server"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
        self.mcp_server_path = root_path / "mcp-server" / "mcp_server.py"
        self.python_path = sys.executable
        
    async def _call_mcp_server(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call the MCP server using subprocess communication"""
        try:
            # Prepare the MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {}
            }
            
            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                self.python_path,
                str(self.mcp_server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(root_path)
            )
            
            # Send request and get response
            request_data = json.dumps(mcp_request) + "\n"
            stdout, stderr = await process.communicate(request_data.encode())
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "MCP server process failed"
                return {
                    "success": False,
                    "error": f"MCP server error: {error_msg}",
                    "error_type": "mcp_server_error"
                }
            
            # Parse response
            try:
                response_lines = stdout.decode().strip().split('\n')
                # Find the JSON response (skip any log messages)
                for line in response_lines:
                    if line.strip().startswith('{'):
                        mcp_response = json.loads(line.strip())
                        # Check if it's a successful MCP response
                        if "result" in mcp_response:
                            return {
                                "success": True,
                                "result": mcp_response["result"]
                            }
                        elif "error" in mcp_response:
                            return {
                                "success": False,
                                "error": mcp_response["error"].get("message", "MCP server error"),
                                "error_type": "mcp_tool_error"
                            }
                        else:
                            return {
                                "success": True,
                                "result": mcp_response
                            }
                
                return {
                    "success": False,
                    "error": "No valid JSON response from MCP server",
                    "error_type": "response_parse_error"
                }
                
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse MCP server response: {str(e)}",
                    "error_type": "json_parse_error"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to communicate with MCP server: {str(e)}",
                "error_type": "communication_error"
            }
    
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
        """Get list of available tools from secure MCP server"""
        tools = [
            {
                "name": "query_mall_data",
                "description": "Secure query mall database using natural language with AI-powered extraction and SQL injection prevention.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Natural language query about malls (e.g., 'find malls in District 1 with rent under $1000')"
                        }
                    },
                    "required": ["message"]
                },
                "security_features": [
                    "SQL injection prevention",
                    "Input validation",
                    "Parameterized queries", 
                    "Response sanitization"
                ]
            }
        ]
        
        return {
            "tools": tools,
            "status": "operational" if self.api_key else "api_key_missing",
            "security_enabled": True
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments"""
        if tool_name == "query_mall_data":
            if not self.api_key:
                print("Cannot access")
                raise Exception("Internal error")
            
            message = arguments.get("message", "")
            if not message.strip():
                return {
                    "success": False,
                    "error": "No message provided for mall query.",
                    "error_type": "validation_error"
                }
            
            try:
                # Validate input message first
                from .input_validator import InputValidator
                
                is_valid, error_msg = InputValidator.validate_query_message(message)
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "input_validation_error"
                    }
                
                mcp_response = await self._call_mcp_server(
                    "tools/call",
                    {
                        "name": "query_mall_data",
                        "arguments": {"message": message}
                    }
                )
                
                # Handle MCP server response
                if not mcp_response.get("success", False):
                    return {
                        "success": False,
                        "error": mcp_response.get("error", "MCP server returned unsuccessful response"),
                        "error_type": mcp_response.get("error_type", "mcp_server_error")
                    }
                
                # Extract the tool result from MCP response
                tool_result = mcp_response.get("result", {})
                if isinstance(tool_result, dict) and "content" in tool_result:
                    # Parse the content if it's a string containing JSON
                    content = tool_result["content"]
                    if isinstance(content, str):
                        try:
                            import json
                            parsed_content = json.loads(content)
                            return parsed_content
                        except json.JSONDecodeError:
                            return {
                                "success": True,
                                "message": content,
                                "raw_response": True
                            }
                    else:
                        return content
                
                # Return the tool result as-is if it's already structured
                return tool_result
                
            except ImportError as e:
                return {
                    "success": False,
                    "error": f"Failed to import input validator: {str(e)}",
                    "error_type": "import_error"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error processing query: {str(e)}",
                    "error_type": "processing_error"
                }
        else:
            raise Exception(f"Unknown tool '{tool_name}'")

mcp_manager = MCPServerManager()