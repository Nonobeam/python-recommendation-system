from typing import List, Optional

from pydantic import BaseModel, Field


class BoothRecommendationRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier (UUID)")
    category_id: Optional[str] = Field(None, description="Category identifier for filtering")
    min_size: Optional[float] = Field(None, ge=0, description="Minimum booth size in m²")
    max_size: Optional[float] = Field(None, ge=0, description="Maximum booth size in m²")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum rental price")
    preferred_districts: Optional[List[str]] = Field(None, description="Preferred district names")
    preferred_floors: Optional[List[int]] = Field(None, description="Preferred floor levels")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    size: Optional[int] = Field(10, ge=1, le=100, description="Number of results per page")


class BoothRecommendationItem(BaseModel):
    mall_id: str = Field(..., description="Mall identifier")
    mall_name: Optional[str] = Field(None, description="Mall name")
    mall_logo: Optional[str] = Field(None, description="Mall logo URL")
    mall_address: Optional[str] = Field(None, description="Mall address")
    size_m2: Optional[float] = Field(None, description="Booth size in square meters")
    rent_price: Optional[float] = Field(None, description="Current rental price")


class BoothRecommendationResponse(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more results")
    results: List[BoothRecommendationItem] = Field(..., description="List of recommended booths")
