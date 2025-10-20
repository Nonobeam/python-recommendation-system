class RecommendationError(Exception):
    """Base exception for recommendation system errors"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class InsufficientDataError(RecommendationError):
    """Exception raised when there's insufficient data for recommendations"""
    
    def __init__(self, data_type: str, minimum_required: int = None):
        self.data_type = data_type
        self.minimum_required = minimum_required
        if minimum_required:
            message = f"Insufficient {data_type} data: at least {minimum_required} records required"
        else:
            message = f"Insufficient {data_type} data for generating recommendations"
        super().__init__(message)

class FeatureExtractionError(RecommendationError):
    """Exception raised when feature extraction fails"""
    
    def __init__(self, feature_name: str, entity_id: str, message: str = None):
        self.feature_name = feature_name
        self.entity_id = entity_id
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Failed to extract feature '{feature_name}' for entity '{entity_id}'")

class ModelTrainingError(RecommendationError):
    """Exception raised when model training fails"""
    
    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        super().__init__(f"Model training failed for '{model_name}': {message}")

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

class TrafficAnalysisError(RecommendationError):
    """Exception raised when traffic analysis fails"""
    
    def __init__(self, location_id: str, message: str = None):
        self.location_id = location_id
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Traffic analysis failed for location '{location_id}'")

class BudgetCompatibilityError(RecommendationError):
    """Exception raised when budget compatibility check fails"""
    
    def __init__(self, business_id: str, mall_id: str, message: str = None):
        self.business_id = business_id
        self.mall_id = mall_id
        if message:
            super().__init__(message)
        else:
            super().__init__(f"Budget compatibility check failed for business '{business_id}' and mall '{mall_id}'")