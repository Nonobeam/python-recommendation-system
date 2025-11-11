from enum import Enum


class ActionType(Enum):
    """Enum for different types of user actions that can be logged in search history"""

    SEARCH_MALL = "search_mall"
    SEARCH_BUSINESS = "search_business"
    VIEW_DETAILS = "view_details"
    FILTER_RESULTS = "filter_results"
    EXPORT_DATA = "export_data"

    def __str__(self):
        return self.value

    @classmethod
    def get_all_values(cls):
        """Get all enum values as a list"""
        return [action.value for action in cls]
