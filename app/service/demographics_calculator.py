from typing import Any, Dict

from sqlalchemy.orm import Session


class DemographicsCalculator:
    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_mall_demographics(self, mall_id: str) -> Dict[str, Any]:
        return None

    def calculate_business_demographics(self, business_id: str) -> Dict[str, Any]:
        return None
