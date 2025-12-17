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


class NoAvailableBoothsError(RecommendationError):
    """Exception raised when a mall has no available booths for brand recommendations"""

    def __init__(self, mall_id: str, message: str = None):
        self.mall_id = mall_id
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Mall '{mall_id}' has no available booths for brand recommendations")


class NoActiveCommissionContractError(RecommendationError):
    """Exception raised when a mall has no active commission contract"""

    def __init__(self, mall_id: str, message: str = None):
        self.mall_id = mall_id
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Mall '{mall_id}' has no active commission contract")
