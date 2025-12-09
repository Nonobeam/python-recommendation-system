from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.config.elasticsearch import AISearchService, ElasticsearchService
from app.model.error_code import ErrorCode
from app.model.exception_mapper import map_exception_to_error_code
from app.service.input_validator import InputValidator
from app.utils.logger import api_logger


class SearchService:
    """Service for handling search operations with booth index"""

    def __init__(self):
        self.elasticsearch_service = ElasticsearchService()
        self.ai_search_service = AISearchService()

    def _get_booth_images(self, booth_ids: List[str]) -> Dict[str, Optional[str]]:
        """
        Query database to get imageUrl for booths from booth_visual_assets table.
        Only returns images where displayOrder == 0 and assetType == 'IMAGE'.

        Args:
            booth_ids: List of booth IDs to fetch images for

        Returns:
            Dictionary mapping booth_id to imageUrl (or None if not found)
        """
        if not booth_ids:
            return {}

        db: Session = next(get_db())
        try:
            placeholders = ",".join([f":booth_id_{i}" for i in range(len(booth_ids))])
            query = text(
                f"""
                SELECT
                    bva.booth_id,
                    bva.file_url as image_url
                FROM platform_service.booth_visual_assets bva
                WHERE bva.booth_id IN ({placeholders})
                    AND bva.display_order = 0
                    AND bva.asset_type = 'IMAGE'
            """
            )

            params = {f"booth_id_{i}": booth_id for i, booth_id in enumerate(booth_ids)}

            results = db.execute(query, params).fetchall()

            image_map = {}
            for row in results:
                image_map[row.booth_id] = row.image_url

            return image_map

        except Exception as e:
            api_logger.error(f"Error fetching booth images: {str(e)}")
            return {}
        finally:
            db.close()

    def _check_rental_status(self, booth_ids: List[str]) -> Dict[str, bool]:
        """
        Check if booths are currently rented by looking for active rental_information records.

        Args:
            booth_ids: List of booth IDs to check rental status for

        Returns:
            Dictionary mapping booth_id to rental status (True if rented, False otherwise)
        """
        if not booth_ids:
            return {}

        db: Session = next(get_db())
        try:
            placeholders = ",".join([f":booth_id_{i}" for i in range(len(booth_ids))])
            query = text(
                f"""
                SELECT DISTINCT ri.booth_id
                FROM platform_service.rental_information ri
                WHERE ri.booth_id IN ({placeholders})
                AND ri.is_current = true
            """
            )

            params = {f"booth_id_{i}": booth_id for i, booth_id in enumerate(booth_ids)}

            results = db.execute(query, params).fetchall()
            rented_booth_ids = {row.booth_id for row in results}

            rental_map = {booth_id: booth_id in rented_booth_ids for booth_id in booth_ids}

            return rental_map

        except Exception as e:
            api_logger.error(f"Error checking rental status: {str(e)}")
            return {booth_id: False for booth_id in booth_ids}
        finally:
            db.close()

    async def search_booths(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 10,
        brand_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any], Optional[ErrorCode], Optional[str]]:
        """
        Search booths using AI-powered natural language processing and Elasticsearch.
        This method handles validation, AI extraction, and Elasticsearch querying.

        Returns:
            Tuple of (success: bool, data: dict, error_code: Optional[ErrorCode], error_message: Optional[str])
        """
        try:
            is_valid, error_message = InputValidator.validate_query_message(query)
            if not is_valid:
                api_logger.warning(f"Invalid search query: {error_message}")
                return False, {}, ErrorCode.VALIDATION_ERROR, error_message

            sanitized_query = InputValidator.sanitize_message(query)
            if not sanitized_query:
                api_logger.warning("Failed to sanitize query")
                return False, {}, ErrorCode.VALIDATION_ERROR, "Invalid query format"

            results = await self.elasticsearch_service.search_booths_with_ai(
                brand_id=brand_id,
                query=sanitized_query,
                ai_service=self.ai_search_service,
                page=page_number,
                size=page_size,
            )

            if results["success"]:
                raw_results = results.get("results", [])
                booth_ids = [booth.get("booth_id") for booth in raw_results if booth.get("booth_id")]
                image_map = self._get_booth_images(booth_ids)
                rental_map = self._check_rental_status(booth_ids)

                formatted_results = []
                for booth in raw_results:
                    enriched_booth = booth.copy()
                    enriched_booth["mall_logo"] = booth.get("mall_logo") or booth.get("logo")
                    enriched_booth["mall_address"] = booth.get("mall_address") or booth.get("address")
                    booth_id = booth.get("booth_id")
                    enriched_booth["imageUrl"] = image_map.get(booth_id) if booth_id else None
                    enriched_booth["is_rented"] = rental_map.get(booth_id, False) if booth_id else False
                    formatted_results.append(enriched_booth)

                pagination_info = results.get("pagination") or {
                    "pageNumber": results.get("page", page_number),
                    "pageSize": results.get("size", page_size),
                    "totalResults": results["total_found"],
                    "totalPages": (results["total_found"] + page_size - 1) // page_size,
                    "hasMore": results.get("has_more", False),
                }

                response_data = {
                    "extracted_criteria": results["extracted_criteria"],
                    "pagination": pagination_info,
                    "results": formatted_results,
                }
                return True, response_data, None, None
            else:
                error_msg = results.get("error", "Unknown error")
                api_logger.error(f"AI search failed: {error_msg}")

                if "Gemini API error: API request failed with status 503" in error_msg:
                    return (
                        False,
                        {},
                        ErrorCode.GEMINI_API_ERROR,
                        "AI search service is temporarily unavailable. Please try again later.",
                    )
                elif "AI extraction failed" in error_msg:
                    return (
                        False,
                        {},
                        ErrorCode.GEMINI_API_ERROR,
                        "AI processing service is currently unavailable. Please try again later.",
                    )
                else:
                    return False, {}, ErrorCode.SERVICE_UNAVAILABLE, f"Search failed: {error_msg}"

        except Exception as e:
            api_logger.error(f"Unexpected error in search: {str(e)}")
            error_code, message = map_exception_to_error_code(e)
            return False, {}, error_code, message
