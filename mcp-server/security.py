"""
Security validation module for SQL injection prevention and input sanitization
"""
import re
from typing import Dict, Any, List, Optional, Union
from config import SecurityConfig, DatabaseConfig, QueryFieldType

class SecurityValidator:
    """Handles security validation and SQL injection prevention"""
    
    @staticmethod
    def sanitize_string_value(value: str, max_length: int = None) -> Optional[str]:
        """Sanitize string value and check for malicious content"""
        if not isinstance(value, str):
            return None
            
        value = value.strip()
        
        if max_length and len(value) > max_length:
            return None
            
        value_lower = value.lower()
        for keyword in SecurityConfig.BLOCKED_KEYWORDS:
            if keyword in value_lower:
                return None
                
        if not re.match(SecurityConfig.ALLOWED_CHARS_PATTERN, value):
            return None
            
        return value
    
    @staticmethod
    def validate_numeric_value(value: Union[int, float], min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric value ranges"""
        if not isinstance(value, (int, float)):
            return False
            
        if min_val is not None and value < min_val:
            return False
            
        if max_val is not None and value > max_val:
            return False
            
        return True
    
    @staticmethod
    def validate_query_message(message: str) -> bool:
        """Basic message validation for MCP server"""
        if not isinstance(message, str):
            return False
            
        message = message.strip()
        
        if len(message) < SecurityConfig.MIN_MESSAGE_LENGTH or len(message) > SecurityConfig.MAX_MESSAGE_LENGTH:
            return False
            
        message_lower = message.lower()
        for keyword in SecurityConfig.BLOCKED_KEYWORDS:
            if keyword in message_lower:
                return False
                
        return True
    
    @staticmethod
    def validate_extracted_criteria(criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize extracted query criteria"""
        if not isinstance(criteria, dict):
            return {}
            
        if len(criteria) > SecurityConfig.MAX_CRITERIA_COUNT:
            return {}
            
        validated_criteria = {}
        
        for field, value in criteria.items():
            base_field = field
            
            if field.endswith('_min'):
                base_field = field[:-4]
            elif field.endswith('_max'):
                base_field = field[:-4]
            
            if base_field not in DatabaseConfig.ALLOWED_FIELDS:
                continue
                
            field_config = DatabaseConfig.ALLOWED_FIELDS[base_field]
            field_type = field_config['type']
            
            if field_type == QueryFieldType.STRING:
                max_length = field_config.get('max_length', SecurityConfig.MAX_STRING_LENGTH)
                sanitized_value = SecurityValidator.sanitize_string_value(str(value), max_length)
                if sanitized_value:
                    validated_criteria[field] = sanitized_value
                    
            elif field_type in [QueryFieldType.INTEGER, QueryFieldType.FLOAT]:
                try:
                    numeric_value = float(value) if field_type == QueryFieldType.FLOAT else int(value)
                    min_val = field_config.get('min_value')
                    max_val = field_config.get('max_value')
                    
                    if SecurityValidator.validate_numeric_value(numeric_value, min_val, max_val):
                        validated_criteria[field] = numeric_value
                except (ValueError, TypeError):
                    continue
                    
            elif field_type == QueryFieldType.BOOLEAN:
                if isinstance(value, bool):
                    validated_criteria[field] = value
                elif isinstance(value, str) and value.lower() in ['true', 'false']:
                    validated_criteria[field] = value.lower() == 'true'
        
        return validated_criteria

class QueryBuilder:
    """Builds safe SQL queries using parameterized statements"""
    
    @staticmethod
    def build_mall_query(criteria: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build safe parameterized SQL query for mall search"""
        if not criteria:
            return "SELECT * FROM malls LIMIT 100", {}
        
        where_clauses = []
        parameters = {}
        param_counter = 0
        
        for field, value in criteria.items():
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            # Handle range queries
            if field.endswith('_min'):
                base_field = field[:-4]
                if base_field in DatabaseConfig.RANGE_FIELDS:
                    where_clauses.append(f"{base_field} >= :{param_name}")
                    parameters[param_name] = value
                    
            elif field.endswith('_max'):
                base_field = field[:-4]
                if base_field in DatabaseConfig.RANGE_FIELDS:
                    where_clauses.append(f"{base_field} <= :{param_name}")
                    parameters[param_name] = value
                    
            # Handle exact match
            elif field in DatabaseConfig.EXACT_MATCH_FIELDS:
                where_clauses.append(f"{field} = :{param_name}")
                parameters[param_name] = value
                
            # Handle text search
            elif field in DatabaseConfig.TEXT_SEARCH_FIELDS:
                where_clauses.append(f"{field} ILIKE :{param_name}")
                parameters[param_name] = f"%{value}%"
        
        # Build final query
        base_query = "SELECT * FROM malls"
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += " LIMIT 100"  # Always limit results
        
        return base_query, parameters
    
    @staticmethod
    def validate_query_syntax(query: str) -> bool:
        """Basic validation of query syntax for additional safety"""
        query_lower = query.lower().strip()
        
        # Must start with SELECT
        if not query_lower.startswith('select'):
            return False
            
        # Must contain FROM malls
        if 'from malls' not in query_lower:
            return False
            
        # Must have LIMIT
        if 'limit' not in query_lower:
            return False
            
        # Check for dangerous keywords
        dangerous_patterns = [
            'drop', 'delete', 'truncate', 'insert', 'update', 'alter',
            'create', 'grant', 'revoke', 'union', '--', '/*'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False
                
        return True

class ResponseSanitizer:
    """Sanitizes database response data"""
    
    @staticmethod
    def sanitize_mall_data(mall_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize mall data before returning to user"""
        sanitized_data = []
        
        for mall in mall_data:
            if not isinstance(mall, dict):
                continue
                
            sanitized_mall = {}
            
            for field, value in mall.items():
                # Only include allowed fields
                if field in DatabaseConfig.ALLOWED_FIELDS or field in ['id', 'mall_id', 'created_at', 'updated_at']:
                    # Sanitize string values
                    if isinstance(value, str):
                        sanitized_value = SecurityValidator.sanitize_string_value(value)
                        if sanitized_value is not None:
                            sanitized_mall[field] = sanitized_value
                    else:
                        sanitized_mall[field] = value
            
            if sanitized_mall:  # Only add if not empty
                sanitized_data.append(sanitized_mall)
        
        return sanitized_data
    
    @staticmethod
    def create_error_response(error_message: str, error_type: str = "validation_error") -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "error_type": error_type,
            "malls": [],
            "total_found": 0
        }
    
    @staticmethod
    def create_success_response(malls: List[Dict[str, Any]], total_found: int = None) -> Dict[str, Any]:
        """Create standardized success response"""
        if total_found is None:
            total_found = len(malls)
            
        return {
            "success": True,
            "malls": malls,
            "total_found": total_found
        }