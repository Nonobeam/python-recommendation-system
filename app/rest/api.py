from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from pydantic import BaseModel
from ..service.traffic import get_top_matches, get_matches_for_mall, get_matches_for_business
from ..service.mcp_tools import MCPToolService
from ..exception.cache_exceptions import (
    RedisConnectionError, 
    RedisOperationError, 
    CacheError, 
    DemographicDataError, 
    BusinessDataError
)

class GeminiContentRequest(BaseModel):
    text: str
    operation: Optional[str] = "generateContent"
    max_output_tokens: Optional[int] = 2048
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 64

app = FastAPI(
    title="Mall-Business Recommendation API",
    description="API for matching malls with businesses based on demographics, traffic, and budget",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Mall-Business Recommendation API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation-api"}

@app.get("/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top recommendations to return"),
    use_cache: bool = Query(default=True, description="Whether to use cached data")
):
    try:
        recommendations = get_top_matches(limit=limit, use_cache=use_cache)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except DemographicDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing demographic data: {str(e)}")
    except BusinessDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing business data: {str(e)}")
    except RedisConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Cache service unavailable: {str(e)}")
    except RedisOperationError as e:
        raise HTTPException(status_code=500, detail=f"Cache operation failed: {str(e)}")
    except CacheError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/recommendations/mall/{mall_id}")
async def get_recommendations_for_mall(
    mall_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations for this mall"),
    use_cache: bool = Query(default=True, description="Whether to use cached data")
):
    try:
        recommendations = get_matches_for_mall(mall_id=mall_id, limit=limit, use_cache=use_cache)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "mall_id": mall_id,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except DemographicDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing demographic data: {str(e)}")
    except BusinessDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing business data: {str(e)}")
    except RedisConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Cache service unavailable: {str(e)}")
    except RedisOperationError as e:
        raise HTTPException(status_code=500, detail=f"Cache operation failed: {str(e)}")
    except CacheError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations for mall: {str(e)}")

@app.get("/recommendations/business/{business_id}")
async def get_recommendations_for_business(
    business_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of mall recommendations for this business"),
    use_cache: bool = Query(default=True, description="Whether to use cached data")
):
    try:
        recommendations = get_matches_for_business(business_id=business_id, limit=limit, use_cache=use_cache)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "business_id": business_id,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except DemographicDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing demographic data: {str(e)}")
    except BusinessDataError as e:
        raise HTTPException(status_code=400, detail=f"Missing business data: {str(e)}")
    except RedisConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Cache service unavailable: {str(e)}")
    except RedisOperationError as e:
        raise HTTPException(status_code=500, detail=f"Cache operation failed: {str(e)}")
    except CacheError as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations for business: {str(e)}")

@app.post("/cache/demographics")
async def cache_demographics():
    try:
        from ..config.db import get_db
        from ..service.demographics_calculator import DemographicsCalculator
        
        db_gen = get_db()
        db = next(db_gen)
        try:
            calculator = DemographicsCalculator(db)
            results = calculator.cache_all_demographics()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Demographics calculation and caching completed",
                    "results": results
                }
            )
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error caching demographics: {str(e)}")

@app.get("/cache/status")
async def get_cache_status():
    try:
        from ..datastore.cache_manager import get_cache_status
        
        status = get_cache_status()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "cache_status": status
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cache status: {str(e)}")

@app.get("/mcp/tools", response_model=List[Dict])
async def get_mcp_tools():
    """Get list of available MCP tools"""
    try:
        from ..service.mcp_client import mcp_manager
        
        tools_data = await mcp_manager.get_available_tools()
        tools = tools_data.get("tools", [])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(tools),
                "tools": tools
            }
        )
    except Exception as e:
        # Fallback to static tools if MCP manager is not available
        tools = MCPToolService.get_available_tools()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(tools),
                "tools": tools,
                "note": f"Using static tools due to error: {str(e)}"
            }
        )

@app.get("/mcp/tools/{tool_name}")
async def get_mcp_tool_details(tool_name: str):
    """Get details for a specific MCP tool"""
    try:
        tool = MCPToolService.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "tool": tool
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tool details: {str(e)}")

@app.get("/mcp/status")
async def get_mcp_server_status():
    """Get MCP server status and configuration"""
    try:
        status = MCPToolService.get_server_status()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "status": status
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving MCP server status: {str(e)}")

@app.post("/mcp/generate-content")
async def generate_content_with_gemini(request: GeminiContentRequest):
    """Generate content using Gemini API through MCP server with configurable parameters"""
    try:
        from ..service.mcp_client import mcp_manager

        # Validate input
        text = request.text
        operation = request.operation
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text parameter cannot be empty")
        
        # Validate token limits
        if request.max_output_tokens < 1 or request.max_output_tokens > 8192:
            raise HTTPException(status_code=400, detail="max_output_tokens must be between 1 and 8192")
        
        if not (0.0 <= request.temperature <= 2.0):
            raise HTTPException(status_code=400, detail="temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= request.top_p <= 1.0):
            raise HTTPException(status_code=400, detail="top_p must be between 0.0 and 1.0")
        
        if request.top_k < 1 or request.top_k > 100:
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 100")
        
        # Use MCP server to generate content with parameters
        result = await mcp_manager.generate_content(
            text=text, 
            operation=operation,
            max_output_tokens=request.max_output_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "operation": operation,
                "input_text": text,
                "generation_config": {
                    "max_output_tokens": request.max_output_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "top_k": request.top_k
                },
                "result": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content via MCP: {str(e)}")