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

@app.post("/mcp/query-malls")
async def query_malls_with_ai(request: dict):
    """Query mall database using natural language through AI"""
    try:
        from ..service.mcp_client import mcp_manager

        # Validate input
        message = request.get("message", "")
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message parameter cannot be empty")
        
        # Use MCP server to query malls with AI
        result = await mcp_manager.call_tool("query_mall_data", {"message": message})
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "query": message,
                "result": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying malls via AI: {str(e)}")