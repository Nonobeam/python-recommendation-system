"""
Configuration module for MCP server security and validation
"""
import os
from typing import Dict, List, Set, Any
from enum import Enum

class QueryFieldType(Enum):
    """Supported field types for database queries"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

class SecurityConfig:
    """Security configuration for SQL injection prevention"""
    
    # Maximum query length to prevent large payloads
    MAX_QUERY_LENGTH = 1000
    
    # Maximum number of search criteria
    MAX_CRITERIA_COUNT = 10
    
    # Blocked keywords that could indicate SQL injection attempts
    BLOCKED_KEYWORDS = {
        'drop', 'delete', 'truncate', 'insert', 'update', 'alter', 
        'create', 'grant', 'revoke', 'exec', 'execute', 'union',
        'select', 'from', 'where', 'join', 'having', 'group by',
        'order by', '--', '/*', '*/', ';', 'xp_', 'sp_', 'sqlcmd'
    }
    
    # Allowed characters pattern for string values
    ALLOWED_CHARS_PATTERN = r'^[a-zA-Z0-9\s\-_.,()&]+$'
    
    # Maximum string field length
    MAX_STRING_LENGTH = 255
    
    # Numeric value ranges
    MIN_PRICE = 0
    MAX_PRICE = 1000000  # $1M max
    MIN_VISITORS = 0
    MAX_VISITORS = 100000  # 100k max daily visitors
    MIN_PERCENTAGE = 0
    MAX_PERCENTAGE = 100

class DatabaseConfig:
    """Database field configuration and validation rules"""
    
    # Allowed database fields with their types and validation rules
    ALLOWED_FIELDS: Dict[str, Dict[str, Any]] = {
        'name': {
            'type': QueryFieldType.STRING,
            'max_length': 100,
            'description': 'Mall name'
        },
        'type': {
            'type': QueryFieldType.STRING,
            'max_length': 50,
            'description': 'Mall type (shopping center, outlet, etc.)'
        },
        'avg_daily_visitors': {
            'type': QueryFieldType.INTEGER,
            'min_value': SecurityConfig.MIN_VISITORS,
            'max_value': SecurityConfig.MAX_VISITORS,
            'description': 'Average daily visitor count'
        },
        'rent_price_usd': {
            'type': QueryFieldType.FLOAT,
            'min_value': SecurityConfig.MIN_PRICE,
            'max_value': SecurityConfig.MAX_PRICE,
            'description': 'Monthly rent price in USD'
        },
        'management_fee_usd': {
            'type': QueryFieldType.FLOAT,
            'min_value': SecurityConfig.MIN_PRICE,
            'max_value': SecurityConfig.MAX_PRICE,
            'description': 'Monthly management fee in USD'
        },
        'vat_percent': {
            'type': QueryFieldType.FLOAT,
            'min_value': SecurityConfig.MIN_PERCENTAGE,
            'max_value': SecurityConfig.MAX_PERCENTAGE,
            'description': 'VAT percentage'
        },
        'motorbike_fee_vnd': {
            'type': QueryFieldType.INTEGER,
            'min_value': 0,
            'max_value': 1000000,  # 1M VND max
            'description': 'Motorbike parking fee in VND'
        },
        'car_fee_vnd': {
            'type': QueryFieldType.INTEGER,
            'min_value': 0,
            'max_value': 10000000,  # 10M VND max
            'description': 'Car parking fee in VND'
        },
        'electricity_policy': {
            'type': QueryFieldType.STRING,
            'max_length': 200,
            'description': 'Electricity billing policy'
        },
        'overtime_fee_policy': {
            'type': QueryFieldType.STRING,
            'max_length': 200,
            'description': 'Overtime fee policy'
        },
        'lease_term': {
            'type': QueryFieldType.STRING,
            'max_length': 100,
            'description': 'Lease term conditions'
        },
        'deposit_policy': {
            'type': QueryFieldType.STRING,
            'max_length': 200,
            'description': 'Security deposit policy'
        },
        'payment_policy': {
            'type': QueryFieldType.STRING,
            'max_length': 200,
            'description': 'Payment terms and policy'
        },
        'address': {
            'type': QueryFieldType.STRING,
            'max_length': 255,
            'description': 'Full street address'
        },
        'city': {
            'type': QueryFieldType.STRING,
            'max_length': 100,
            'description': 'City name'
        },
        'district': {
            'type': QueryFieldType.STRING,
            'max_length': 100,
            'description': 'District or area name'
        }
    }
    
    # Fields that support range queries (min/max)
    RANGE_FIELDS: Set[str] = {
        'avg_daily_visitors', 'rent_price_usd', 'management_fee_usd', 
        'vat_percent', 'motorbike_fee_vnd', 'car_fee_vnd'
    }
    
    # Fields that support exact match only
    EXACT_MATCH_FIELDS: Set[str] = {
        'name', 'type', 'city', 'district'
    }
    
    # Fields that support partial text search
    TEXT_SEARCH_FIELDS: Set[str] = {
        'name', 'address', 'electricity_policy', 'overtime_fee_policy',
        'lease_term', 'deposit_policy', 'payment_policy'
    }

class GeminiConfig:
    """Gemini API configuration"""
    
    # API settings
    API_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
    
    # Generation parameters for query extraction
    QUERY_EXTRACTION_CONFIG = {
        "maxOutputTokens": 500,  # Limit output for query extraction
        "temperature": 0.1,      # Low temperature for consistent extraction
        "topP": 0.9,
        "topK": 40
    }
    
    # Timeout for API calls
    API_TIMEOUT = 15.0
    
    # System prompt for query extraction
    QUERY_EXTRACTION_PROMPT = """
You are a mall database query assistant. Extract search criteria from user messages and return only a JSON object with field names and values.

Allowed fields: {allowed_fields}

Rules:
1. Only use the allowed field names listed above
2. For numeric fields, extract min/max ranges when mentioned
3. For text fields, extract exact or partial matches
4. Return only valid JSON, no explanations
5. If no valid criteria found, return empty object {{}}

Examples:
- "malls in District 1" → {{"district": "District 1"}}
- "rent under $1000" → {{"rent_price_usd_max": 1000}}
- "parking fee between 50000 and 100000 VND" → {{"motorbike_fee_vnd_min": 50000, "motorbike_fee_vnd_max": 100000}}

User message: {user_message}

Extract criteria as JSON:
"""

def get_allowed_fields_description() -> str:
    """Get formatted description of allowed fields"""
    descriptions = []
    for field, config in DatabaseConfig.ALLOWED_FIELDS.items():
        field_type = config['type'].value
        desc = config['description']
        descriptions.append(f"- {field} ({field_type}): {desc}")
    
    return "\n".join(descriptions)