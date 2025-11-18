from typing import List, Optional

from pydantic import BaseModel, Field


class BrandRecommendationItem(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    brand_name: Optional[str] = Field(None, description="Brand name")
    brand_logo: Optional[str] = Field(None, description="Brand logo URL")
    final_score: float = Field(..., description="Final compatibility score (0-1)")
    mall_compatibility_score: float = Field(..., description="Brand-mall compatibility score")
    booth_match_score: Optional[float] = Field(None, description="Best booth match score")
    component_scores: Optional[dict] = Field(None, description="Component score breakdown")
    explanations: Optional[List[str]] = Field(None, description="Score explanations")
    available_booths_count: int = Field(0, description="Number of available booths matching brand requirements")


class BrandRecommendationResponse(BaseModel):
    mall_id: str = Field(..., description="Mall identifier")
    total_results: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_more: bool = Field(..., description="Whether there are more results")
    results: List[BrandRecommendationItem] = Field(..., description="List of recommended brands")
