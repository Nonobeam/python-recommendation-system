class RecommendationError(Exception):
    """Base exception for recommendation system errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ScoreCalculationError(RecommendationError):
    """Exception raised when score calculation fails"""

    def __init__(self, score_type: str, entity_pair: tuple, message: str = None):
        self.score_type = score_type
        self.entity_pair = entity_pair
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Failed to calculate {score_type} score for entities {entity_pair}")


class DemographicsError(RecommendationError):
    """Exception raised when demographics calculation fails"""

    def __init__(self, entity_id: str, entity_type: str, message: str = None):
        self.entity_id = entity_id
        self.entity_type = entity_type
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Demographics calculation failed for {entity_type} '{entity_id}'")
