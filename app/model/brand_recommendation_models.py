from typing import List, Optional

from pydantic import BaseModel, Field


class BrandRecommendationItem(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    brand_name: Optional[str] = Field(None, description="Brand name")
    brand_logo: Optional[str] = Field(None, description="Brand logo URL")
    phone_number: Optional[str] = Field(None, description="Brand contact phone number")
    mail: Optional[str] = Field(None, description="Brand email address")
    category_name: Optional[str] = Field(None, description="Brand category name")
    short_description: Optional[str] = Field(None, description="Brand short description")
    final_score: int = Field(..., description="Final compatibility score (rounded down)")


class BrandRecommendationResponse(BaseModel):
    mall_id: str = Field(..., description="Mall identifier")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more results")
    results: List[BrandRecommendationItem] = Field(..., description="List of recommended brands")
