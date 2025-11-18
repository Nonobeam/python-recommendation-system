from math import isnan
from typing import Any, Optional


def is_valid_number(value: Any) -> bool:
    """
    Check if a value is a valid number that can be used in calculations.
    Returns False for None, NaN, or non-numeric types.
    """
    if value is None:
        return False
    if isinstance(value, (int, float)):
        if isnan(value):
            return False
        return True
    return False


def safe_get_number(data: dict, key: str, default: Optional[float] = None) -> Optional[float]:
    """
    Safely get a number from a dictionary, returning None if the value is invalid.
    """
    value = data.get(key, default)
    if is_valid_number(value):
        return float(value)
    return None
