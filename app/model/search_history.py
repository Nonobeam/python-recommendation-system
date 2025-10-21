import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.config.db import get_db
from app.model.models import SearchHistory
from app.model.action_type import ActionType
from app.utils.logger import get_app_logger

logger = get_app_logger("search_history")

def save_search_history(
    user_id: str, 
    action_type: ActionType, 
    search_query: Optional[str] = None,
    brand_id: Optional[str] = None,
) -> bool:
    """Save search history to database"""
    db = None
    try:
        db = next(get_db())
        
        search_history = SearchHistory(
            search_history_id=str(uuid.uuid4()),
            user_id=user_id,
            search_query=search_query,
            brand_id=brand_id,
            action_type=action_type.value,
            created_at=datetime.utcnow()
        )
        
        db.add(search_history)
        db.commit()
        
        logger.info(f"Saved search history for user {user_id}, action: {action_type.value}, brand: {brand_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save search history: {str(e)}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def get_user_search_history(
    user_id: str, 
    limit: int = 100,
    action_type: Optional[ActionType] = None,
    brand_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get search history for a user"""
    db = None
    try:
        db = next(get_db())
        
        query = db.query(SearchHistory).filter(SearchHistory.user_id == user_id)
        
        if action_type:
            query = query.filter(SearchHistory.action_type == action_type.value)
        
        if brand_id:
            query = query.filter(SearchHistory.brand_id == brand_id)
        
        search_history = query.order_by(SearchHistory.created_at.desc()).limit(limit).all()
        
        results = []
        for history in search_history:
            results.append({
                "search_history_id": history.search_history_id,
                "user_id": history.user_id,
                "search_query": history.search_query,
                "brand_id": history.brand_id,
                "action_type": history.action_type,
                "created_at": history.created_at
            })
        
        logger.info(f"Retrieved {len(results)} search history records for user {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to get search history: {str(e)}")
        return []
    finally:
        if db:
            db.close()

def get_brand_search_history(brand_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get search history for a specific brand (backward compatibility)"""
    db = None
    try:
        db = next(get_db())
        
        search_history = db.query(SearchHistory)\
            .filter(SearchHistory.brand_id == brand_id)\
            .filter(SearchHistory.action_type == ActionType.SEARCH_MALL.value)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        results = []
        for history in search_history:
            results.append({
                "brand_search_history_id": history.search_history_id,  # For backward compatibility
                "brand_id": history.brand_id,
                "search_value": history.search_query,  # For backward compatibility
                "created_at": history.created_at
            })
        
        logger.info(f"Retrieved {len(results)} brand search history records for brand {brand_id}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to get brand search history: {str(e)}")
        return []
    finally:
        if db:
            db.close()

def get_search_analytics(
    user_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Get search analytics for user or brand"""
    db = None
    try:
        db = next(get_db())
        
        from datetime import timedelta
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(SearchHistory).filter(SearchHistory.created_at >= since_date)
        
        if user_id:
            query = query.filter(SearchHistory.user_id == user_id)
        
        if brand_id:
            query = query.filter(SearchHistory.brand_id == brand_id)
        
        total_searches = query.count()
        
        # Group by action type
        action_counts = {}
        for action in ActionType:
            count = query.filter(SearchHistory.action_type == action.value).count()
            action_counts[action.value] = count
        
        analytics = {
            "total_searches": total_searches,
            "action_breakdown": action_counts,
            "period_days": days,
            "user_id": user_id,
            "brand_id": brand_id
        }
        
        logger.info(f"Generated analytics for user {user_id}, brand {brand_id}: {total_searches} searches in {days} days")
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {str(e)}")
        return {}
    finally:
        if db:
            db.close()