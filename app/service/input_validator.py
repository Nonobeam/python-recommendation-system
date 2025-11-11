"""
Input validation module for MCP client - simple message validation
"""

import re
from typing import Optional


class InputValidator:
    """Simple input validation for MCP client messages"""

    # Basic security patterns
    BLOCKED_KEYWORDS = [
        "drop",
        "delete",
        "truncate",
        "insert",
        "update",
        "alter",
        "create",
        "grant",
        "revoke",
        "union",
        "exec",
        "execute",
        "script",
        "javascript",
        "vbscript",
        "<script",
        "</script>",
        "onload",
        "onerror",
        "onclick",
        "javascript:",
        "vbscript:",
        "data:",
        "base64",
        "eval(",
        "settimeout",
        "setinterval",
    ]

    # Sensitive information patterns
    SENSITIVE_PATTERNS = [
        r"password\s*[:=]\s*\w+",
        r"api[_\s]*key\s*[:=]\s*[\w\-]+",
        r"token\s*[:=]\s*[\w\-\.]+",
        r"secret\s*[:=]\s*\w+",
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card pattern
        r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",  # SSN pattern
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\s|$)",  # Email pattern (partial)
    ]

    # Mall-related keywords that indicate relevant queries
    MALL_KEYWORDS = [
        "mall",
        "shopping",
        "center",
        "store",
        "shop",
        "retail",
        "rent",
        "price",
        "cost",
        "fee",
        "lease",
        "district",
        "location",
        "address",
        "visitor",
        "traffic",
        "business",
        "tenant",
        "space",
        "area",
        "floor",
        "building",
    ]

    MAX_MESSAGE_LENGTH = 1000
    MIN_MESSAGE_LENGTH = 3

    @staticmethod
    def sanitize_message(message: str) -> Optional[str]:
        """Basic message sanitization"""
        if not isinstance(message, str):
            return None

        # Remove excessive whitespace
        message = re.sub(r"\s+", " ", message.strip())

        # Check length limits
        if len(message) < InputValidator.MIN_MESSAGE_LENGTH:
            return None
        if len(message) > InputValidator.MAX_MESSAGE_LENGTH:
            return None

        # Remove dangerous characters but keep basic punctuation
        message = re.sub(r"[<>{}[\]\\|`~]", "", message)

        return message

    @staticmethod
    def contains_blocked_keywords(message: str) -> bool:
        """Check if message contains blocked keywords"""
        message_lower = message.lower()
        for keyword in InputValidator.BLOCKED_KEYWORDS:
            if keyword in message_lower:
                return True
        return False

    @staticmethod
    def contains_sensitive_info(message: str) -> bool:
        """Check if message contains sensitive information"""
        for pattern in InputValidator.SENSITIVE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def is_mall_related(message: str) -> bool:
        """Check if message is related to mall/shopping queries"""
        message_lower = message.lower()

        # Check for mall-related keywords
        for keyword in InputValidator.MALL_KEYWORDS:
            if keyword in message_lower:
                return True

        # Check for location/search patterns
        location_patterns = [
            r"find\s+\w+",
            r"search\s+\w+",
            r"show\s+me\s+\w+",
            r"list\s+\w+",
            r"get\s+\w+",
            r"where\s+\w+",
            r"how\s+many\s+\w+",
            r"what\s+\w+",
        ]

        for pattern in location_patterns:
            if re.search(pattern, message_lower):
                return True

        return False

    @staticmethod
    def validate_query_message(message: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive validation of query message
        Returns (is_valid, error_message)
        """
        # Basic sanitization
        sanitized = InputValidator.sanitize_message(message)
        if not sanitized:
            return False, "Invalid message format or length"

        # Check for blocked keywords
        if InputValidator.contains_blocked_keywords(sanitized):
            return False, "Message contains prohibited content"

        # Check for sensitive information
        if InputValidator.contains_sensitive_info(sanitized):
            return False, "Message may contain sensitive information"

        if not InputValidator.is_mall_related(sanitized):
            # For now, just allow non-mall queries but could log this
            pass

        return True, None
