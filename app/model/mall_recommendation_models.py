from typing import List, Optional

from pydantic import BaseModel, Field


class MallRecommendationItem(BaseModel):
    mall_id: str = Field(..., description="Mall identifier")
    mall_name: Optional[str] = Field(None, description="Mall name")
    mall_logo: Optional[str] = Field(None, description="Mall logo URL")
    mall_address: Optional[str] = Field(None, description="Mall address")
    final_score: float = Field(..., description="Final compatibility score (0-1)")
    component_scores: Optional[dict] = Field(None, description="Component score breakdown")
    explanations: Optional[List[str]] = Field(None, description="Score explanations")


class MallRecommendationResponse(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more results")
    results: List[MallRecommendationItem] = Field(..., description="List of recommended malls")
