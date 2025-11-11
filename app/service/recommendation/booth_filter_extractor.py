from typing import Any, Dict, Optional

from app.config.elasticsearch import AISearchService
from app.model.search_history import get_brand_search_history
from app.service.recommendation.repositories import BrandDemographicDataSource
from app.utils.logger import api_logger


class BoothFilterExtractor:
    def __init__(self):
        self.ai_service = AISearchService()

    async def extract_filters_from_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Extract booth recommendation filters from brand demographics and search history.

        Returns a dictionary with filter parameters:
        - category_id: From brand operational profile
        - min_size, max_size: From brand space requirements
        - max_price: From brand financial capacity
        - preferred_floors: From brand requirements or inferred from search history
        - preferred_districts: Inferred from search history using AI
        """
        filters: Dict[str, Any] = {}

        brand_data = BrandDemographicDataSource.get_by_id(brand_id)
        if not brand_data:
            api_logger.warning(f"Brand demographics not found for brand_id={brand_id}")
            return filters

        brand_meta = brand_data.get("meta_data", brand_data)

        op = brand_meta.get("operational_profile", {})
        fc = brand_meta.get("financial_capacity", {})
        req = brand_meta.get("requirements", {})

        category = op.get("category")
        if category:
            filters["category_id"] = self._extract_category_id(category)

        space_required = op.get("space_requirement_m2", 0)
        if space_required and space_required > 0:
            size_tolerance = 0.2
            filters["min_size"] = space_required * (1 - size_tolerance)
            filters["max_size"] = space_required * (1 + size_tolerance)

        max_affordable_rent = fc.get("max_affordable_rent", 0)
        if max_affordable_rent and max_affordable_rent > 0:
            filters["max_price"] = max_affordable_rent

        preferred_floors = req.get("preferred_floors", [])
        if preferred_floors:
            filters["preferred_floors"] = preferred_floors

        search_history_filters = await self._extract_filters_from_search_history(brand_id)
        filters.update(search_history_filters)

        api_logger.info(f"Extracted filters for brand {brand_id}: {filters}")
        return filters

    async def _extract_filters_from_search_history(self, brand_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Extract filter preferences from brand search history using AI.

        Analyzes recent search queries to infer:
        - Preferred districts
        - Preferred floors (if mentioned)
        - Size preferences (if mentioned)
        - Price preferences (if mentioned)
        """
        filters: Dict[str, Any] = {}

        try:
            search_history = get_brand_search_history(brand_id, limit=limit)
            if not search_history:
                return filters

            search_queries = [
                history.get("search_value") or history.get("search_query")
                for history in search_history
                if history.get("search_value") or history.get("search_query")
            ]

            if not search_queries:
                return filters

            combined_query = " ".join(search_queries[:5])
            ai_result = await self.ai_service.extract_search_criteria(combined_query)

            if ai_result.get("success") and ai_result.get("criteria"):
                criteria = ai_result["criteria"]

                if "preferred_districts" in criteria:
                    filters["preferred_districts"] = criteria["preferred_districts"]
                elif "district" in criteria:
                    district = criteria["district"]
                    if isinstance(district, list):
                        filters["preferred_districts"] = district
                    else:
                        filters["preferred_districts"] = [district]

                if "preferred_floors" in criteria:
                    floors = criteria["preferred_floors"]
                    if isinstance(floors, list):
                        filters["preferred_floors"] = floors
                    else:
                        filters["preferred_floors"] = [floors]
                elif "floor" in criteria:
                    floor = criteria["floor"]
                    if isinstance(floor, list):
                        filters["preferred_floors"] = floor
                    elif isinstance(floor, int):
                        filters["preferred_floors"] = [floor]

                if "min_size" in criteria or "size" in criteria:
                    size_info = criteria.get("min_size") or criteria.get("size")
                    if isinstance(size_info, dict):
                        filters["min_size"] = size_info.get("min") or size_info.get("gte")
                    elif isinstance(size_info, (int, float)):
                        filters["min_size"] = size_info

                if "max_size" in criteria or "size" in criteria:
                    size_info = criteria.get("max_size") or criteria.get("size")
                    if isinstance(size_info, dict):
                        filters["max_size"] = size_info.get("max") or size_info.get("lte")
                    elif isinstance(size_info, (int, float)):
                        filters["max_size"] = size_info

                if "max_price" in criteria or "price" in criteria:
                    price_info = criteria.get("max_price") or criteria.get("price")
                    if isinstance(price_info, dict):
                        filters["max_price"] = price_info.get("max") or price_info.get("lte")
                    elif isinstance(price_info, (int, float)):
                        filters["max_price"] = price_info

        except Exception as e:
            api_logger.warning(f"Failed to extract filters from search history for brand {brand_id}: {str(e)}")

        return filters

    def _extract_category_id(self, category: str) -> Optional[str]:
        """
        Extract category ID from category name.

        This is a simplified mapping. In production, this should query
        the categories table to get the actual category_id.
        """
        category_lower = category.lower() if category else ""
        category_mapping = {
            "restaurant": "food",
            "cafe": "food",
            "food": "food",
            "f&b": "food",
            "retail": "shop",
            "clothing": "shop",
            "shop": "shop",
            "service": "service",
        }

        for key, value in category_mapping.items():
            if key in category_lower:
                return value

        return None
