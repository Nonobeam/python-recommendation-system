from typing import Any, Dict, Optional, Tuple

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
                formatted_results = []
                for booth in raw_results:
                    enriched_booth = booth.copy()
                    enriched_booth["mall_logo"] = booth.get("mall_logo") or booth.get("logo")
                    enriched_booth["mall_address"] = booth.get("mall_address") or booth.get("address")
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
