from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PaginationInfo(BaseModel):
    """Pagination information for search results"""
    current_page: int = Field(..., description="Current page number", example=1)
    page_size: int = Field(..., description="Number of results per page", example=10)
    total_results: int = Field(..., description="Total number of results found", example=25)
    total_pages: int = Field(..., description="Total number of pages", example=3)
    has_more: bool = Field(..., description="Whether there are more results available", example=True)

class MallSearchResult(BaseModel):
    """Individual mall search result"""
    mall_id: str = Field(..., description="Unique mall identifier", example="mall_123")
    mall_name: str = Field(..., description="Name of the mall", example="Premium Shopping Center")
    mall_type: Optional[str] = Field(None, description="Type of mall (Premium, Standard, Budget)", example="Premium")
    district: Optional[str] = Field(None, description="District location", example="District 1")
    rent_price_usd: Optional[float] = Field(None, description="Rental price in USD", example=1200.0)
    management_fee_usd: Optional[float] = Field(None, description="Management fee in USD", example=150.0)
    avg_daily_visitors: Optional[int] = Field(None, description="Average daily visitors", example=8000)
    facilities: Optional[List[str]] = Field(None, description="Available facilities", example=["parking", "elevator"])
    score: Optional[float] = Field(None, description="Relevance score (0-1)", example=0.95)

class SearchCriteria(BaseModel):
    """Extracted search criteria from AI processing"""
    mall_type: Optional[str] = Field(None, description="Mall type filter", example="Premium")
    district: Optional[str] = Field(None, description="District filter", example="District 1")
    min_rent_price: Optional[float] = Field(None, description="Minimum rent price in USD", example=500.0)
    max_rent_price: Optional[float] = Field(None, description="Maximum rent price in USD", example=2000.0)
    min_management_fee: Optional[float] = Field(None, description="Minimum management fee in USD", example=100.0)
    max_management_fee: Optional[float] = Field(None, description="Maximum management fee in USD", example=300.0)
    min_visitors: Optional[int] = Field(None, description="Minimum daily visitors", example=5000)
    facilities: Optional[List[str]] = Field(None, description="Required facilities", example=["parking", "elevator"])

class MallSearchResponse(BaseModel):
    """Response model for mall search API"""
    success: bool = Field(..., description="Whether the search was successful", example=True)
    user_id: str = Field(..., description="ID of the user who performed the search", example="user_12345")
    brand_id: Optional[str] = Field(None, description="Brand ID from JWT token", example="brand_67890")
    original_query: str = Field(..., description="Original search query", example="premium malls with parking")
    extracted_criteria: SearchCriteria = Field(..., description="AI-extracted search criteria")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    results: List[MallSearchResult] = Field(..., description="Array of mall search results")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type or category", example="Authentication required")
    detail: str = Field(..., description="Detailed error message", example="Invalid or expired JWT token")

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status", example="healthy")
    service: str = Field(..., description="Service name", example="mall-recommendation-system")
    version: str = Field(..., description="Service version", example="1.0.0")
    timestamp: str = Field(..., description="Response timestamp", example="2025-10-21T04:00:00Z")

class TokenInfo(BaseModel):
    """Token information extracted from JWT"""
    user_id: str = Field(..., description="User identifier", example="user_12345")
    brand_id: Optional[str] = Field(None, description="Brand identifier", example="brand_67890")
    role: Optional[str] = Field(None, description="User role", example="admin")
    email: Optional[str] = Field(None, description="User email", example="user@example.com")

class SearchHistoryEntry(BaseModel):
    """Search history entry"""
    search_history_id: str = Field(..., description="Unique history entry ID")
    user_id: str = Field(..., description="User identifier")
    brand_id: Optional[str] = Field(None, description="Brand identifier")
    action_type: str = Field(..., description="Type of action performed")
    query: Optional[str] = Field(None, description="Search query text")
    results_count: Optional[int] = Field(None, description="Number of results returned")
    created_at: datetime = Field(..., description="When the action was performed")

class SearchHistoryResponse(BaseModel):
    """Response model for search history API"""
    success: bool = Field(True, description="Whether the request was successful")
    user_id: str = Field(..., description="User identifier")
    brand_id: Optional[str] = Field(None, description="Brand identifier")
    total_searches: int = Field(..., description="Total number of searches")
    history: List[SearchHistoryEntry] = Field(..., description="Search history entries")