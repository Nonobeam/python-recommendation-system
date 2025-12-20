import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from app.exception.custom_exceptions import AIProcessingError, GeminiAPIError, MCPValidationError
from app.utils.logger import elasticsearch_logger

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None


class AISearchService:
    """Service for AI-powered search query processing using Gemini API"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = os.getenv(
            "GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        )

        if not self.api_key:
            raise MCPValidationError("GEMINI_API_KEY environment variable is required")

    async def extract_search_criteria(self, query: str) -> Dict[str, Any]:
        """Extract structured search criteria from natural language query"""
        try:
            if not query or len(query.strip()) == 0:
                return {"success": False, "error": "Empty query provided"}

            if len(query) > 1000:
                return {"success": False, "error": "Query too long (max 1000 characters)"}

            system_prompt = self._get_system_prompt()
            user_message = f"Extract search criteria from this query: {query}"

            response = await self._call_gemini_api(system_prompt, user_message)

            if response["success"]:
                criteria = self._parse_criteria_response(response["content"])
                return {"success": True, "criteria": criteria}
            else:
                return {"success": False, "error": response["error"]}

        except Exception as e:
            return {"success": False, "error": f"AI processing failed: {str(e)}"}

    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI criteria extraction"""
        return """
            You are a search criteria extraction assistant for a mall database system.
            Extract search parameters from natural language queries and return them as structured JSON.

            Always normalize and convert user queries into a canonical search form before returning.
            Vietnamese addresses generally follow this structure: number + street + ward (optional) + district + city.
            Extract these parts whenever possible, and keep them in Vietnamese without translating to English.
            For example, convert "Ở quận 10 trên đường Nguyễn Huệ" into structured fields like
            {"street": "đường Nguyễn Huệ", "district": "quận 10", "city": "Thành phố Hồ Chí Minh"}.
            Do not simply echo back the raw user text when building the criteria, but preserve the language.

            IMPORTANT - NEARBY LOCATION INTELLIGENCE:
            When users use proximity keywords like "gần" (near/nearby), "lân cận" (adjacent), "xung quanh" (around),
            you should intelligently EXPAND the district search to include adjacent/nearby districts.

            Ho Chi Minh City, Vietnam - Current District Adjacency Map (as of 2025):
            NOTE: This represents the current administrative divisions of Ho Chi Minh City (Thành phố Hồ Chí Minh), Vietnam.
            - Quận 1: neighboring districts are Quận 3, Quận 4, Quận 5, Quận Bình Thạnh
            - Quận 2 (Thủ Đức): neighboring districts are Quận 1, Quận 9, Quận Bình Thạnh, Quận Thủ Đức
            - Quận 3: neighboring districts are Quận 1, Quận 5, Quận 10, Quận Bình Thạnh, Quận Phú Nhuận
            - Quận 4: neighboring districts are Quận 1, Quận 7, Quận 8
            - Quận 5: neighboring districts are Quận 1, Quận 3, Quận 6, Quận 8, Quận 10, Quận 11
            - Quận 6: neighboring districts are Quận 5, Quận 8, Quận 11, Quận Bình Tân
            - Quận 7: neighboring districts are Quận 4, Quận 8, Huyện Nhà Bè
            - Quận 8: neighboring districts are Quận 4, Quận 5, Quận 6, Quận 7, Huyện Bình Chánh
            - Quận 9 (Thủ Đức): neighboring districts are Quận 2, Quận Thủ Đức, Huyện Dĩ An (Bình Dương)
            - Quận 10: neighboring districts are Quận 3, Quận 5, Quận 11, Quận Tân Bình
            - Quận 11: neighboring districts are Quận 5, Quận 6, Quận 10, Quận Tân Bình, Quận Tân Phú
            - Quận 12: neighboring districts are Huyện Hóc Môn, Quận Tân Bình, Quận Gò Vấp
            - Quận Bình Tân: neighboring districts are Quận 6, Quận Tân Phú, Huyện Bình Chánh
            - Quận Bình Thạnh: neighboring districts are Quận 1, Quận 2, Quận 3, Quận Phú Nhuận, Quận Thủ Đức
            - Quận Gò Vấp: neighboring districts are Quận 12, Quận Phú Nhuận, Quận Tân Bình, Quận Thủ Đức
            - Quận Phú Nhuận: neighboring districts are Quận 3, Quận Bình Thạnh, Quận Gò Vấp, Quận Tân Bình
            - Quận Tân Bình: neighboring districts are Quận 10, Quận 11, Quận 12, Quận Gò Vấp, Quận Phú Nhuận, Quận Tân Phú
            - Quận Tân Phú: neighboring districts are Quận 11, Quận 12, Quận Bình Tân, Quận Tân Bình
            - Quận Thủ Đức: neighboring districts are Quận 2, Quận 9, Quận Bình Thạnh, Quận Gò Vấp

            Examples of nearby search expansion:
            - Query: "trung tâm mua sắm gần quận 1"
              → Extract: {"district": ["quận 1", "quận 3", "quận 4", "quận 5", "quận Bình Thạnh"], "general_search": "trung tâm mua sắm"}
            - Query: "mall near district 7"
              → Extract: {"district": ["quận 7", "quận 4", "quận 8", "huyện Nhà Bè"], "general_search": "mall"}
            - Query: "lân cận quận Tân Bình"
              → Extract: {"district": ["quận Tân Bình", "quận 10", "quận 11", "quận 12", "quận Gò Vấp",
              "quận Phú Nhuận", "quận Tân Phú"], "general_search": ""}

            Available mall fields:
            - mall_name (string): Mall name
            - mall_type (string): Mall type (Premium, Standard, Outlet, etc.)
            - avg_daily_visitors (number): Average daily visitor count
            - management_fee_usd (number): Management fee in USD
            - motorbike_fee_vnd (number): Motorbike parking fee in VND
            - car_fee_vnd (number): Car parking fee in VND
            - electricity_policy (string): Electricity policy details
            - overtime_fee_policy (string): Overtime fee policy
            - lease_term (string): Lease term information
            - deposit_policy (string): Deposit policy details
            - payment_policy (string): Payment policy information
            - number_of_floors (number): Number of floors
            - total_floor_area_m2 (number): Total floor area in square meters
            - opening_year (number): Year the mall opened
            - parking_motorbike_spaces (number): Number of motorbike parking spaces
            - parking_car_spaces (number): Number of car parking spaces
            - has_public_transport_access (boolean): Has public transport access
            - has_loading_dock (boolean): Has loading dock
            - has_elevator (boolean): Has elevator
            - has_escalator (boolean): Has escalator
            - operating_hours_weekday (string): Weekday operating hours
            - operating_hours_weekend (string): Weekend operating hours
            - contact_phone (string): Contact phone number
            - contact_email (string): Contact email
            - website (string): Website URL

            Available booth fields:
            - booth_name (string): Booth name
            - floor_name (string): Floor name
            - floor_description (string): Floor description
            - zone_description (string): Zone description
            - category_name (string): Category name (e.g., "Dịch vụ - Làm đẹp & Spa")
            - booth_description (string): Booth description
            - shape (string): Booth shape (e.g., "Hình vuông", "Hình chữ nhật")
            - size_m2 (number): Booth size in square meters
            - ceiling_height_m (number): Ceiling height in meters
            - frontage_width_m (number): Frontage width in meters
            - storage_area_m2 (number): Storage area in square meters
            - electricity_capacity_kw (number): Electricity capacity in kilowatts
            - has_windows (boolean): Has windows
            - has_column_obstacles (boolean): Has column obstacles
            - has_water_supply (boolean): Has water supply
            - has_gas_line (boolean): Has gas line
            - has_drainage (boolean): Has drainage
            - has_ventilation (boolean): Has ventilation
            - has_grease_trap (boolean): Has grease trap
            - has_internet (boolean): Has internet
            - has_storage_area (boolean): Has storage area
            - rent_price (number): Booth rental price in VND

            IMPORTANT - VIETNAMESE PRICE UNDERSTANDING:
            In Vietnam, people commonly use "triệu" to mean million VND.
            When users mention prices with "triệu", convert them to the full number in VND:
            - "4 triệu" → rent_price: 4000000 (or range if context implies approximate)
            - "dưới 5 triệu" or "< 5 triệu" → rent_price: {"lte": 5000000}
            - "trên 3 triệu" or "> 3 triệu" → rent_price: {"gte": 3000000}
            - "từ 2 đến 5 triệu" or "2-5 triệu" → rent_price: {"gte": 2000000, "lte": 5000000}
            - "khoảng 4 triệu" or "tầm 4 triệu" → rent_price: {"gte": 3000000, "lte": 5000000}
            Examples:
            - Query: "booth giá 4 triệu" → {"general_search": "booth", "rent_price": 4000000}
            - Query: "tìm booth dưới 10 triệu" → {"general_search": "booth", "rent_price": {"lte": 10000000}}
            - Query: "booth 5-8 triệu quận 1" → {"general_search": "booth", "rent_price": {"gte": 5000000, "lte": 8000000}, "district": "quận 1"}

            Return ONLY a JSON object with extracted criteria. Always include a "general_search"
            field that contains the normalized search text you want Elasticsearch to use (not the
            original raw query), and add any structured fields you can extract. Always keep
            general_search in Vietnamese if the user queried in Vietnamese. Use these structures:
            - For text fields: {"field_name": "search_value"}
            - For numeric ranges: {"field_name": {"min": value, "max": value}} or {"field_name": {"gte": value}} or {"field_name": {"lte": value}}
            - For exact numeric matches: {"field_name": exact_value}
            - For boolean fields: {"field_name": true/false}
            - For multiple text options: {"field_name": ["option1", "option2"]}

            Example responses:
            {
              "general_search": "các trung tâm thương mại cao cấp ở quận 1",
              "district": "quận 1",
              "mall_name": "central",
              "avg_daily_visitors": {"gte": 5000},
              "has_elevator": true
            }
            {
              "general_search": "trung tâm thương mại trên đường Nguyễn Huệ",
              "street": "đường Nguyễn Huệ",
              "mall_type": ["Premium", "Standard"],
              "management_fee_usd": {"max": 1000}
            }
            {
              "general_search": "trung tâm mua sắm hiện đại mở sau năm 2010",
              "city": "Thành phố Hồ Chí Minh",
              "opening_year": {"gte": 2010},
              "number_of_floors": {"min": 3}
            }

            If no specific structured criteria can be extracted, still return a JSON object
            with a single field "general_search" whose value is your normalized internal
            search phrase, not the exact original query text from the user.
            """

    async def _call_gemini_api(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Call Gemini API for AI processing"""
        try:
            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser query: {user_message}"}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1000},
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {"success": True, "content": content}
                else:
                    raise GeminiAPIError(
                        f"API request failed with status {response.status_code}",
                        response.status_code,
                        response.json() if response.content else None,
                    )

        except GeminiAPIError:
            raise
        except Exception as e:
            raise AIProcessingError(f"API call failed: {str(e)}", e)

    def _parse_criteria_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response to extract criteria JSON"""
        try:
            content = content.strip()

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                criteria = json.loads(json_str)

                validated_criteria = self._validate_criteria(criteria)
                return validated_criteria
            else:
                return {"general_search": content}

        except json.JSONDecodeError:
            return {"general_search": content}
        except Exception:
            return {"general_search": content}

    def _validate_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize extracted criteria"""
        valid_fields = {
            # Mall fields
            "mall_name",
            "mall_type",
            "avg_daily_visitors",
            "management_fee_usd",
            "motorbike_fee_vnd",
            "car_fee_vnd",
            "electricity_policy",
            "overtime_fee_policy",
            "lease_term",
            "deposit_policy",
            "payment_policy",
            "number_of_floors",
            "total_floor_area_m2",
            "opening_year",
            "parking_motorbike_spaces",
            "parking_car_spaces",
            "has_public_transport_access",
            "has_loading_dock",
            "has_elevator",
            "has_escalator",
            "operating_hours_weekday",
            "operating_hours_weekend",
            "contact_phone",
            "contact_email",
            "website",
            # Booth fields
            "booth_name",
            "floor_name",
            "floor_description",
            "zone_description",
            "category_name",
            "booth_description",
            "shape",
            "size_m2",
            "ceiling_height_m",
            "frontage_width_m",
            "storage_area_m2",
            "electricity_capacity_kw",
            "has_windows",
            "has_column_obstacles",
            "has_water_supply",
            "has_gas_line",
            "has_drainage",
            "has_ventilation",
            "has_grease_trap",
            "has_internet",
            "has_storage_area",
            "rent_price",
            # Location fields
            "street",
            "district",
            "ward",
            "city",
            "address",
            "general_search",
        }

        validated = {}
        for key, value in criteria.items():
            if key in valid_fields:
                validated[key] = self._sanitize_value(key, value)

        return validated

    def _sanitize_value(self, field: str, value: Any) -> Any:
        """Sanitize individual field values"""
        boolean_fields = {
            # Mall boolean fields
            "has_public_transport_access",
            "has_loading_dock",
            "has_elevator",
            "has_escalator",
            # Booth boolean fields
            "has_windows",
            "has_column_obstacles",
            "has_water_supply",
            "has_gas_line",
            "has_drainage",
            "has_ventilation",
            "has_grease_trap",
            "has_internet",
            "has_storage_area",
        }
        numeric_fields = {
            # Mall numeric fields
            "avg_daily_visitors",
            "management_fee_usd",
            "motorbike_fee_vnd",
            "car_fee_vnd",
            "number_of_floors",
            "total_floor_area_m2",
            "opening_year",
            "parking_motorbike_spaces",
            "parking_car_spaces",
            # Booth numeric fields
            "size_m2",
            "ceiling_height_m",
            "frontage_width_m",
            "storage_area_m2",
            "electricity_capacity_kw",
            "rent_price",
        }

        if field in boolean_fields:
            return bool(value) if isinstance(value, (bool, int)) else False
        elif field in numeric_fields:
            if isinstance(value, dict):
                sanitized = {}
                for op, val in value.items():
                    if op in ["min", "max", "gte", "lte", "gt", "lt"] and isinstance(val, (int, float)):
                        sanitized[op] = float(val) if field in ["management_fee_usd"] else int(val)
                return sanitized if sanitized else 0
            elif isinstance(value, (int, float)):
                return float(value) if field in ["management_fee_usd"] else int(value)
        elif isinstance(value, str):
            return re.sub(r'[<>"\';\\]', "", value)[:500]
        elif isinstance(value, list):
            return [re.sub(r'[<>"\';\\]', "", str(item))[:100] for item in value[:10]]

        return value


class ElasticsearchService:
    """Service for Elasticsearch operations and AI-powered search"""

    def __init__(self):
        self.host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.port = int(os.getenv("ELASTICSEARCH_PORT", 9200))
        self.protocol = os.getenv("ELASTICSEARCH_PROTOCOL", "http")
        self.url = f"{self.protocol}://{self.host}:{self.port}"
        self._client = None

    def get_client(self):
        """Get Elasticsearch client with proper configuration"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """Create Elasticsearch client based on configuration"""
        if Elasticsearch is None:
            raise ImportError("Elasticsearch library not installed")

        client_params = {"hosts": [self.url]}

        username = os.getenv("ELASTICSEARCH_USERNAME")
        password = os.getenv("ELASTICSEARCH_PASSWORD")
        api_key = os.getenv("ELASTICSEARCH_API_KEY")

        if username and password:
            client_params["basic_auth"] = (username, password)
        elif api_key:
            client_params["api_key"] = api_key

        if self.protocol == "https":
            ca_certs_path = os.getenv("ELASTICSEARCH_CA_CERTS")
            cert_fingerprint = os.getenv("ELASTICSEARCH_CERT_FINGERPRINT")

            if ca_certs_path:
                client_params["ca_certs"] = ca_certs_path
            elif cert_fingerprint:
                client_params["ssl_assert_fingerprint"] = cert_fingerprint

        return Elasticsearch(**client_params)

    def test_connection(self) -> bool:
        """Test if connection to Elasticsearch is successful"""
        try:
            client = self.get_client()
            info = client.info()
            elasticsearch_logger.info(f"Connected to Elasticsearch cluster: {info.get('cluster_name', 'Unknown')}")
            return True
        except Exception as e:
            elasticsearch_logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            return False

    async def search_malls_with_ai(
        self, brand_id: str, query: str, ai_service: AISearchService, page: int = 1, size: int = 10
    ) -> dict:
        """Main function: Extract criteria using AI, then query Elasticsearch"""
        try:
            extraction_result = await ai_service.extract_search_criteria(query)

            if not extraction_result["success"]:
                return {"success": False, "error": f"AI extraction failed: {extraction_result['error']}", "results": []}

            criteria = extraction_result["criteria"]

            search_result = self.search_malls_with_ai_criteria(criteria, page, size)
            total_found = search_result.get("total", 0)
            pagination = {
                "pageNumber": search_result.get("page", page),
                "pageSize": search_result.get("size", size),
                "totalResults": total_found,
                "totalPages": (total_found + size - 1) // size if size else 0,
                "hasMore": search_result.get("has_more", False),
            }

            return {
                "success": search_result["success"],
                "original_query": query,
                "extracted_criteria": criteria,
                "total_found": total_found,
                "page": page,
                "size": size,
                "pagination": pagination,
                "results": search_result.get("results", []),
                "error": search_result.get("error"),
            }

        except Exception as e:
            return {"success": False, "error": f"Search operation failed: {str(e)}", "results": []}

    async def search_booths_with_ai(
        self, brand_id: Optional[str], query: str, ai_service: AISearchService, page: int = 1, size: int = 10
    ) -> dict:
        """Main function: Extract criteria using AI, then query Elasticsearch for booths"""
        try:
            extraction_result = await ai_service.extract_search_criteria(query)

            if not extraction_result["success"]:
                return {"success": False, "error": f"AI extraction failed: {extraction_result['error']}", "results": []}

            criteria = extraction_result["criteria"]

            search_result = self.search_booths_with_ai_criteria(criteria, page, size)
            total_found = search_result.get("total", 0)
            pagination = {
                "pageNumber": search_result.get("page", page),
                "pageSize": search_result.get("size", size),
                "totalResults": total_found,
                "totalPages": (total_found + size - 1) // size if size else 0,
                "hasMore": search_result.get("has_more", False),
            }

            return {
                "success": search_result["success"],
                "original_query": query,
                "extracted_criteria": criteria,
                "total_found": total_found,
                "page": page,
                "size": size,
                "pagination": pagination,
                "results": search_result.get("results", []),
                "error": search_result.get("error"),
            }

        except Exception as e:
            return {"success": False, "error": f"Search operation failed: {str(e)}", "results": []}

    def search_malls_with_ai_criteria(self, criteria: Dict[str, Any], page: int = 1, size: int = 10) -> dict:
        """Search malls using AI-extracted structured criteria with pagination"""
        try:
            client = self.get_client()

            # Calculate offset for pagination (page 1 = from 0, page 2 = from 10, etc.)
            from_offset = (page - 1) * size

            query_parts = []

            if "general_search" in criteria:
                query_parts.append(self._build_general_search_query(criteria["general_search"]))
            else:
                query_parts = self._build_structured_query(criteria)

            if not query_parts:
                search_body = {"query": {"match_all": {}}, "from": from_offset, "size": size}
            else:
                search_body = {
                    "query": {"bool": {"must": query_parts}},
                    "from": from_offset,
                    "size": size,
                    "_source": self._get_source_fields(),
                }

            response = client.search(index="mall", body=search_body)

            total_hits = response["hits"]["total"]["value"]
            returned_results = len(response["hits"]["hits"])

            elasticsearch_logger.debug(
                f"AI-powered search - Total hits: {total_hits}, Page: {page}, Size: {size}, From: {from_offset}"
            )

            return {
                "success": True,
                "total": total_hits,
                "page": page,
                "size": size,
                "from": from_offset,
                "returned": returned_results,
                "has_more": from_offset + returned_results < total_hits,
                "results": [{**hit["_source"], "_score": hit["_score"]} for hit in response["hits"]["hits"]],
            }

        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def search_booths_with_ai_criteria(self, criteria: Dict[str, Any], page: int = 1, size: int = 10) -> dict:
        """Search booths using AI-extracted structured criteria with pagination"""
        try:
            client = self.get_client()

            from_offset = (page - 1) * size

            query_parts = []

            structured_parts = self._build_structured_booth_query(criteria)
            query_parts.extend(structured_parts)

            if "general_search" in criteria and criteria["general_search"]:
                query_parts.append(self._build_general_booth_search_query(criteria["general_search"]))

            if not query_parts:
                search_body = {"query": {"match_all": {}}, "from": from_offset, "size": size}
            else:
                search_body = {
                    "query": {"bool": {"must": query_parts}},
                    "from": from_offset,
                    "size": size,
                    "_source": self._get_booth_source_fields(),
                }

            response = client.search(index="booth", body=search_body)

            total_hits = response["hits"]["total"]["value"]
            returned_results = len(response["hits"]["hits"])

            elasticsearch_logger.debug(
                f"AI-powered booth search - Total hits: {total_hits}, Page: {page}, Size: {size}, From: {from_offset}"
            )

            return {
                "success": True,
                "total": total_hits,
                "page": page,
                "size": size,
                "from": from_offset,
                "returned": returned_results,
                "has_more": from_offset + returned_results < total_hits,
                "results": [{**hit["_source"], "_score": hit["_score"]} for hit in response["hits"]["hits"]],
            }

        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def _build_structured_booth_query(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build structured Elasticsearch query for booths from AI-extracted criteria"""
        query_parts = []

        for field, value in criteria.items():
            if field == "general_search":
                continue

            if field in {"street", "district", "ward", "city", "address"}:
                mapped_field = "mall_address"
                if isinstance(value, str):
                    query_parts.append(
                        {
                            "match": {
                                mapped_field: {
                                    "query": value,
                                    "operator": "and",
                                    "fuzziness": "AUTO",
                                }
                            }
                        }
                    )
                elif isinstance(value, list):
                    sub_queries = []
                    for item in value:
                        sub_queries.append(
                            {
                                "match": {
                                    mapped_field: {
                                        "query": item,
                                        "operator": "and",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            }
                        )
                    if sub_queries:
                        query_parts.append({"bool": {"should": sub_queries, "minimum_should_match": 1}})
                continue

            if isinstance(value, str):
                if field in ["mall_name", "mall_type", "booth_name", "category_name"]:
                    query_parts.append({"multi_match": {"query": value, "fields": [field], "fuzziness": "AUTO"}})
                else:
                    query_parts.append({"wildcard": {f"{field}.keyword": f"*{value}*"}})

            elif isinstance(value, list):
                should_queries = []
                for item in value:
                    if field in ["mall_name", "mall_type", "booth_name", "category_name"]:
                        should_queries.append({"multi_match": {"query": item, "fields": [field], "fuzziness": "AUTO"}})
                    else:
                        should_queries.append({"match": {field: item}})

                if should_queries:
                    query_parts.append({"bool": {"should": should_queries, "minimum_should_match": 1}})

            elif isinstance(value, dict):
                range_query = {}
                for op, val in value.items():
                    if op in ["min", "gte"]:
                        range_query["gte"] = val
                    elif op in ["max", "lte"]:
                        range_query["lte"] = val
                    elif op == "gt":
                        range_query["gt"] = val
                    elif op == "lt":
                        range_query["lt"] = val

                if range_query:
                    query_parts.append({"range": {field: range_query}})

            elif isinstance(value, bool):
                query_parts.append({"term": {field: value}})

            elif isinstance(value, (int, float)):
                query_parts.append({"term": {field: value}})

        return query_parts

    def _build_general_booth_search_query(self, query: str) -> Dict[str, Any]:
        """Build general search query for booths with unstructured queries"""
        return {
            "multi_match": {
                "query": query,
                "fields": [
                    "booth_name^3",
                    "mall_name^3",
                    "mall_address^3",
                    "mall_type^2",
                    "category_name^2",
                    "floor_name",
                    "booth_description",
                    "zone_description",
                    "overtime_fee_policy",
                    "operating_hours_weekday",
                    "operating_hours_weekend",
                    "contact_phone",
                    "contact_email",
                    "website",
                ],
                "fuzziness": "AUTO",
            }
        }

    def _get_booth_source_fields(self) -> List[str]:
        """Get list of fields to return in booth search results"""
        return [
            "booth_id",
            "booth_name",
            "floor_position_reference",
            "size_m2",
            "is_available",
            "booth_verify_status",
            "booth_status",
            "booth_requirement",
            "booth_updated_at",
            "booth_created_at",
            "mall_id",
            "mall_name",
            "mall_type",
            "mall_address",
            "mall_coordinates",
            "mall_logo",
            "mall_status",
            "mall_verify_status",
            "mall_information_id",
            "number_of_floors",
            "total_floor_area_m2",
            "management_fee_usd",
            "motorbike_fee_vnd",
            "car_fee_vnd",
            "overtime_fee_policy",
            "opening_year",
            "operating_hours_weekday",
            "operating_hours_weekend",
            "contact_phone",
            "contact_email",
            "website",
            "parking_motorbike_spaces",
            "parking_car_spaces",
            "has_public_transport_access",
            "has_loading_dock",
            "has_elevator",
            "has_escalator",
            "mall_info_updated_at",
            "floor_id",
            "floor_level",
            "floor_name",
            "floor_description",
            "zone_id",
            "categories_id",
            "category_name",
            "booth_information_id",
            "zone_description",
            "shape",
            "ceiling_height_m",
            "frontage_width_m",
            "has_windows",
            "has_column_obstacles",
            "has_electricity",
            "electricity_capacity_kw",
            "has_water_supply",
            "has_gas_line",
            "has_drainage",
            "has_ventilation",
            "has_grease_trap",
            "has_internet",
            "has_storage_area",
            "storage_area_m2",
            "booth_description",
            "rent_price",
            "updated_at",
        ]

    def _build_structured_query(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build structured Elasticsearch query from AI-extracted criteria"""
        query_parts = []

        for field, value in criteria.items():
            if field == "general_search":
                continue

            if field in {"street", "district", "ward", "city", "address"}:
                mapped_field = "mall_address"
                if isinstance(value, str):
                    query_parts.append(
                        {
                            "match": {
                                mapped_field: {
                                    "query": value,
                                    "operator": "and",
                                    "fuzziness": "AUTO",
                                }
                            }
                        }
                    )
                elif isinstance(value, list):
                    sub_queries = []
                    for item in value:
                        sub_queries.append(
                            {
                                "match": {
                                    mapped_field: {
                                        "query": item,
                                        "operator": "and",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            }
                        )
                    if sub_queries:
                        query_parts.append({"bool": {"should": sub_queries, "minimum_should_match": 1}})
                continue

            if isinstance(value, str):
                if field in ["mall_name", "mall_type"]:
                    query_parts.append({"multi_match": {"query": value, "fields": [field], "fuzziness": "AUTO"}})
                else:
                    query_parts.append({"wildcard": {f"{field}.keyword": f"*{value}*"}})

            elif isinstance(value, list):
                # Handle multiple values with should (OR) logic
                should_queries = []
                for item in value:
                    if field in ["mall_name", "mall_type"]:
                        should_queries.append({"multi_match": {"query": item, "fields": [field], "fuzziness": "AUTO"}})
                    else:
                        should_queries.append({"match": {field: item}})

                if should_queries:
                    query_parts.append({"bool": {"should": should_queries, "minimum_should_match": 1}})

            elif isinstance(value, dict):
                range_query = {}
                for op, val in value.items():
                    if op in ["min", "gte"]:
                        range_query["gte"] = val
                    elif op in ["max", "lte"]:
                        range_query["lte"] = val
                    elif op == "gt":
                        range_query["gt"] = val
                    elif op == "lt":
                        range_query["lt"] = val

                if range_query:
                    query_parts.append({"range": {field: range_query}})

            elif isinstance(value, bool):
                query_parts.append({"term": {field: value}})

            elif isinstance(value, (int, float)):
                query_parts.append({"term": {field: value}})

        return query_parts

    def _build_general_search_query(self, query: str) -> Dict[str, Any]:
        """Build general search query for unstructured queries"""
        return {
            "multi_match": {
                "query": query,
                "fields": [
                    "mall_name^3",
                    "mall_address^3",
                    "mall_type^2",
                    "electricity_policy",
                    "overtime_fee_policy",
                    "lease_term",
                    "deposit_policy",
                    "payment_policy",
                    "operating_hours_weekday",
                    "operating_hours_weekend",
                    "contact_phone",
                    "contact_email",
                    "website",
                ],
                "fuzziness": "AUTO",
            }
        }

    def _get_source_fields(self) -> List[str]:
        """Get list of fields to return in search results"""
        return [
            "mall_id",
            "mall_name",
            "mall_type",
            "mall_logo",
            "logo",
            "mall_coordinates",
            "mall_address",
            "address",
            "updated_at",
            "mall_information_id",
            "number_of_floors",
            "total_floor_area_m2",
            "avg_daily_visitors",
            "management_fee_usd",
            "motorbike_fee_vnd",
            "car_fee_vnd",
            "electricity_policy",
            "overtime_fee_policy",
            "lease_term",
            "deposit_policy",
            "payment_policy",
            "opening_year",
            "operating_hours_weekday",
            "operating_hours_weekend",
            "contact_phone",
            "contact_email",
            "website",
            "parking_motorbike_spaces",
            "parking_car_spaces",
            "has_public_transport_access",
            "has_loading_dock",
            "has_elevator",
            "has_escalator",
        ]


# Global instances
elasticsearch_service = ElasticsearchService()


def startup_elasticsearch_check(connection_string: str = None) -> bool:
    """Startup check for Elasticsearch connection

    Args:
        connection_string: Optional connection URL (e.g., 'http://localhost:9200').
                          If not provided, uses environment variables.
    """
    elasticsearch_logger.info("Checking Elasticsearch connection...")

    try:
        from elasticsearch import Elasticsearch

        if connection_string:
            # Parse connection string to extract protocol, host, and port
            url = connection_string
            # Extract protocol, host, port from connection string for logging
            if "://" in connection_string:
                protocol = connection_string.split("://")[0]
            else:
                protocol = "http"
        else:
            host = os.getenv("ELASTICSEARCH_HOST", "localhost")
            port = int(os.getenv("ELASTICSEARCH_PORT", 9200))
            protocol = os.getenv("ELASTICSEARCH_PROTOCOL", "http")
            url = f"{protocol}://{host}:{port}"

        client_params = {"hosts": [url]}

        username = os.getenv("ELASTICSEARCH_USERNAME")
        password = os.getenv("ELASTICSEARCH_PASSWORD")
        api_key = os.getenv("ELASTICSEARCH_API_KEY")

        if username and password:
            client_params["basic_auth"] = (username, password)
        elif api_key:
            client_params["api_key"] = api_key

        if protocol == "https":
            ca_certs_path = os.getenv("ELASTICSEARCH_CA_CERTS")
            cert_fingerprint = os.getenv("ELASTICSEARCH_CERT_FINGERPRINT")

            if ca_certs_path:
                client_params["ca_certs"] = ca_certs_path
            elif cert_fingerprint:
                client_params["ssl_assert_fingerprint"] = cert_fingerprint

        # Test connection
        client = Elasticsearch(**client_params)
        info = client.info()

        elasticsearch_logger.info(
            f"Elasticsearch connection successful - Cluster: {info.get('cluster_name', 'Unknown')}"
        )
        return True

    except ImportError:
        elasticsearch_logger.warning("Elasticsearch library not installed - search features will be unavailable")
        return False
    except Exception as e:
        elasticsearch_logger.error(f"Elasticsearch startup check failed: {str(e)}")
        return False
