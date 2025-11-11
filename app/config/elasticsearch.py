import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

from app.exception.custom_exceptions import (AIProcessingError, GeminiAPIError,
                                             MCPValidationError)
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

            Return ONLY a JSON object with extracted criteria. Use these structures:
            - For text fields: {"field_name": "search_value"}
            - For numeric ranges: {"field_name": {"min": value, "max": value}} or {"field_name": {"gte": value}} or {"field_name": {"lte": value}}
            - For exact numeric matches: {"field_name": exact_value}
            - For boolean fields: {"field_name": true/false}
            - For multiple text options: {"field_name": ["option1", "option2"]}

            Example responses:
            {"mall_name": "central", "avg_daily_visitors": {"gte": 5000}, "has_elevator": true}
            {"mall_type": ["Premium", "Standard"], "management_fee_usd": {"max": 1000}}
            {"opening_year": {"gte": 2010}, "number_of_floors": {"min": 3}}

            If no specific criteria can be extracted, return: {"general_search": "original_query"}
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
            "general_search",
        }

        validated = {}
        for key, value in criteria.items():
            if key in valid_fields:
                validated[key] = self._sanitize_value(key, value)

        return validated

    def _sanitize_value(self, field: str, value: Any) -> Any:
        """Sanitize individual field values"""
        boolean_fields = {"has_public_transport_access", "has_loading_dock", "has_elevator", "has_escalator"}
        numeric_fields = {
            "avg_daily_visitors",
            "management_fee_usd",
            "motorbike_fee_vnd",
            "car_fee_vnd",
            "number_of_floors",
            "total_floor_area_m2",
            "opening_year",
            "parking_motorbike_spaces",
            "parking_car_spaces",
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

            return {
                "success": search_result["success"],
                "original_query": query,
                "extracted_criteria": criteria,
                "total_found": search_result.get("total", 0),
                "page": page,
                "size": size,
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

    def _build_structured_query(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build structured Elasticsearch query from AI-extracted criteria"""
        query_parts = []

        for field, value in criteria.items():
            if field == "general_search":
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
            "mall_coordinates",
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


def startup_elasticsearch_check() -> bool:
    """Startup check for Elasticsearch connection"""
    elasticsearch_logger.info("Checking Elasticsearch connection...")

    try:
        from elasticsearch import Elasticsearch

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
