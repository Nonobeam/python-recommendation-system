Phase 1: Theoretical Design
1. Problem Framing

This is a matching problem:

Malls (supply side) have booths with attributes: size, location, price, visitor traffic, demographics, past business success.

Businesses (demand side) have needs: space requirement, budget, expected traffic, type of visitors, and prior performance.

Goal: Suggest best-fit matches (Business ↔ Mall) with a score.

2. Data Sources

Mall side:

Booth metadata: floor plan, size, price, availability.

Visitor traffic: aggregated counts (could estimate via video → footfall count).

Historical tenant success (revenue, duration).

Business side:

Requirements: budget, space, traffic capacity.

Past performance in other malls.

Industry type (e.g., F&B, retail, services).

Shared:

Transaction logs (past 3–6 months).

Onboarding history (if Business already exists in a Mall).

3. Techniques to Use

Phase 1 — Low-cost matching (no heavy training yet)

Rule-based + Scoring:

Weighted matching on constraints: budget, space, traffic.

Example: match_score = w1*budget_fit + w2*traffic_fit + w3*category_fit + w4*history_boost.

Search/Indexing layer:

Use Elasticsearch / OpenSearch (ELK) for filtering & scoring queries.

Businesses query malls (or vice versa) → fast retrieval with weighted scoring.

Optional ML later (Phase 2/3)

Collaborative Filtering (CF): Use history of which businesses succeeded in which malls (matrix of Mall × Business).

Content-based Recommender: Match attributes similarity (e.g., Mall traffic pattern vs Business needs).

Hybrid: Combine CF + Content-based.

Train light ML models in Colab or Vast.ai (low cost).

4. Initial Pipeline

Ingestion: Mall + Business upload profiles.

Feature Extraction:

Normalize units (traffic, size, budget).

Encode categorical features (industry type).

Indexing: Store in Elasticsearch for retrieval.

Matching: Rule-based scoring first.

Feedback loop: If a business accepts/rejects → adjust weights.

5. Phase 1 Deliverables

A theoretical framework with:

Data model for Malls & Businesses.

Matching algorithm (rule-based, no ML yet).

Scoring formula.

Search infra (ELK).

# In short:
Phase 1 = Rule-based matching + ELK scoring → low cost, interpretable.
Phase 2 = Add ML recommender (collaborative + content-based).
Phase 3 = Optimize, expand features (traffic video analysis, dynamic pricing, feedback loops).

Current state
# Phrase 2 (what you have now)

Data sources: Mall features (rent, traffic, demographics) + Business features (budget, target customers, etc.).

Math used:

Budget Fit → ratio (business budget / mall rent) → normalized.

Traffic Fit → cosine similarity between mall traffic vector & business traffic need.

Demographic Fit → cosine similarity between mall demographics & business target demographics.

Final score = weighted average of fits.

Nature: deterministic, rule-based scoring → gives you interpretable baseline matches.

# Phrase 3 (how to move to AI/ML)

Goal: instead of fixed formulas, use machine learning to learn the best scoring function from data.

Steps to move:

Feature Engineering

Reuse Phrase 2 features (budget_fit, traffic_fit, demo_fit).

Add raw features (mall size, location embeddings, shop category, historical performance).

Label Collection

Get historical outcomes:

Accepted/Rejected matches.

Revenue after placement.

Duration of rental.

Convert into labels:

Binary classification (Good Match / Bad Match).

Or regression (Match Success Score, e.g. revenue, retention).

Model Training

Use ML algorithms:

Logistic Regression → interpretable baseline.

XGBoost / LightGBM → great for tabular data.

Neural Nets (if you want embeddings for mall–business matching).

Prediction API

Input: business + mall data.

Output: probability of success / ranking score.

Ranking = sort by predicted score.

Evaluation

Metrics: AUC, Precision@K, NDCG (ranking quality).

Compare ML vs Phrase 2 rule-based scoring.

# In short:

Phrase 2 = handcrafted math.

Phrase 3 = learn weights + nonlinear patterns from data.

# Code detail

app/config/db.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pathlib import Path
import os

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_SCHEMA = os.getenv("DB_SCHEMA")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?options=-c%20search_path%3D{DB_SCHEMA}"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

app/config/redis.py
```python
import redis
from dotenv import load_dotenv
import os
import json
from typing import Optional, Any
from pathlib import Path
from ..exception import RedisConnectionError, RedisOperationError

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DECODE_RESPONSES = True

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=REDIS_DECODE_RESPONSES,
    max_connections=20
)

redis_client = redis.Redis(connection_pool=redis_pool)

class RedisCache:
    def __init__(self, client: redis.Redis = redis_client):
        self.client = client
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError as e:
            raise RedisOperationError("get", key, str(e))
        except json.JSONDecodeError as e:
            raise RedisOperationError("get", key, f"JSON decode error: {str(e)}")
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            json_value = json.dumps(value)
            return self.client.setex(key, expire, json_value)
        except redis.RedisError as e:
            raise RedisOperationError("set", key, str(e))
        except json.JSONEncodeError as e:
            raise RedisOperationError("set", key, f"JSON encode error: {str(e)}")

cache = RedisCache()
```

app/datastore/etl.py
```python
import pandas as pd
from ..config.db import SessionLocal
from ..model.models import Mall, Business
from ..exception import DemographicDataError, BusinessDataError
from .cache_manager import (
    get_cached_mall_demographic,
    get_cached_business_data,
    clear_data_cache, 
    get_cache_status
)

def extract_mall_data():
    print("Fetching mall data from database")
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        data = []
        
        for m in malls:
            mall_id = str(m.id)
            
            cached_demographic = get_cached_mall_demographic(mall_id)
            
            if not cached_demographic:
                raise DemographicDataError(mall_id, "mall")
            
            demographic = cached_demographic
            
            data.append({
                "mall_id": m.id,
                "name": m.name,
                "type": m.type,
                "avg_daily_visitors": m.avg_daily_visitors,
                "demographic": demographic,
            })
        
        return pd.DataFrame(data)

def extract_business_data():
    print("Fetching business data from database")
    with SessionLocal() as session:
        businesses = session.query(Business).all()
        data = []
        
        for b in businesses:
            business_id = str(b.id)
            
            cached_business_data = get_cached_business_data(business_id)
            
            if not cached_business_data:
                raise BusinessDataError(business_id)
            
            data.append({
                "business_id": b.id,
                "name": b.name,
                "category": b.category,
                "brand_tier": b.brand_tier,
                "budget": b.budget,
                "required_size": b.required_size,
                "visitor_capacity": b.visitor_capacity,
                "target_demographic": cached_business_data,
            })
        
        return pd.DataFrame(data)

def transform_mall(data: pd.DataFrame):
    return data[["mall_id", "name", "type", "avg_daily_visitors", "demographic"]]

def transform_business(data: pd.DataFrame):
    return data[["business_id", "name", "category", "brand_tier",
                 "budget", "required_size", "visitor_capacity", "target_demographic"]]

def load(data: pd.DataFrame):
    return data.to_dict(orient="records")

def run_etl(use_cache: bool = True):
    """
    Run ETL pipeline with optional caching
    Args:
        use_cache: Whether to use cached data if available
    """
    if not use_cache:
        print("Running ETL without cache")
        clear_data_cache()
    
    # Show cache status
    cache_status = get_cache_status()
    print(f"Cache status: {cache_status}")
    
    malls_raw = extract_mall_data()
    businesses_raw = extract_business_data()
    malls = transform_mall(malls_raw)
    businesses = transform_business(businesses_raw)
    return load(malls), load(businesses)
```

app/datastore/cache_manager.py
```python
from ..config.redis import cache
from ..exception.cache_exceptions import RedisOperationError, CacheError
import os
from dotenv import load_dotenv

load_dotenv()

DEMOGRAPHIC_PREFIX = os.getenv("REDIS_CACHE_DEMOGRAPHIC_KEY_PREFIX")
BUSINESS_PREFIX = os.getenv("REDIS_CACHE_BUSINESS_KEY_PREFIX")

def cache_mall_demographic(mall_id: str, demographic_data: dict, expire: int = 3600):
    cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
    success = cache.set(cache_key, demographic_data, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache demographic data for mall {mall_id}")
    return success

def get_cached_mall_demographic(mall_id: str):
    cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
    cached = cache.get(cache_key)
    if not cached:
        print(f"No cached demographic data for mall {mall_id}")
    return cached

def cache_business_data(business_id: str, business_data: dict, expire: int = 3600):
    cache_key = f"{BUSINESS_PREFIX}{business_id}"
    success = cache.set(cache_key, business_data, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache business data for business {business_id}")
    return success

def get_cached_business_data(business_id: str):
    cache_key = f"{BUSINESS_PREFIX}{business_id}"
    cached = cache.get(cache_key)
    if not cached:
        print(f"No cached business data for business {business_id}")
    return cached

def cache_recommendations(recommendations: list, cache_key: str = "recommendations", expire: int = 1800):
    success = cache.set(cache_key, recommendations, expire=expire)
    if not success:
        raise RedisOperationError(f"Failed to cache recommendations with key: {cache_key}")
    return success

def get_cached_recommendations(cache_key: str = "recommendations"):
    cached = cache.get(cache_key)
    return cached
```

app/service/features.py
```python
import numpy as np

MALL_FEATURES = [
    "avg_daily_visitors",
    "demographic"
]

BUSINESS_FEATURES = [
    "budget",
    "required_size",
    "visitor_capacity",
    "target_demographic"
]

def normalize_demographic_vector(demographic_data, expected_length=19):
    if isinstance(demographic_data, dict):
        values = []
        
        spending_power = demographic_data.get("spending_power", {})
        values.extend([
            spending_power.get("budget", 0),
            spending_power.get("mid_range", 0),
            spending_power.get("premium", 0)
        ])
        
        visit_purpose = demographic_data.get("visit_purpose", {})
        values.extend([
            visit_purpose.get("shopping", 0),
            visit_purpose.get("dining", 0),
            visit_purpose.get("entertainment", 0)
        ])
        
        traffic_pattern = demographic_data.get("traffic_pattern", {})
        values.extend([
            traffic_pattern.get("weekday", 0),
            traffic_pattern.get("weekend", 0),
            traffic_pattern.get("avg_dwell_time_minutes", 0)
        ])
        
        tenant_mix = demographic_data.get("tenant_mix", {})
        values.extend([
            tenant_mix.get("shop_percent", 0),
            tenant_mix.get("food_percent", 0),
            tenant_mix.get("service_percent", 0),
            tenant_mix.get("occupancy_rate", 0)
        ])
        
        historical_performance = demographic_data.get("historical_performance", {})
        values.extend([
            historical_performance.get("avg_tenant_success_rate", 0),
            historical_performance.get("avg_tenant_duration_months", 0),
            historical_performance.get("tenant_turnover_rate", 0)
        ])
        
        market_intelligence = demographic_data.get("market_intelligence", {})
        values.extend([
            market_intelligence.get("similar_malls_nearby", 0),
            market_intelligence.get("catchment_area_population", 0),
            market_intelligence.get("accessibility_score", 0)
        ])
        
        vector = np.array(values, dtype=float)
    else:
        vector = np.array(demographic_data, dtype=float) if demographic_data else np.array([])
    
    if len(vector) < expected_length:
        vector = np.pad(vector, (0, expected_length - len(vector)), 'constant')
    elif len(vector) > expected_length:
        vector = vector[:expected_length]
    
    return vector

def normalize_business_vector(business_data, expected_length=19):
    if isinstance(business_data, dict):
        values = []
        
        proven_performance = business_data.get("proven_performance", {})
        values.extend([
            proven_performance.get("avg_daily_revenue", 0) / 1_000_000,
            proven_performance.get("avg_transaction_value", 0) / 1000,
            proven_performance.get("transaction_frequency", 0),
            proven_performance.get("revenue_per_sqm", 0) / 1000
        ])
        
        requirements = business_data.get("requirements", {})
        values.extend([
            requirements.get("min_traffic_needed", 0),
            requirements.get("budget", 0) / 1_000_000
        ])
        
        business_profile = business_data.get("business_profile", {})
        values.extend([
            business_profile.get("staff_count", 0),
            1 if business_profile.get("requires_kitchen", False) else 0,
            1 if business_profile.get("requires_ventilation", False) else 0
        ])
        
        financial_health = business_data.get("financial_health", {})
        values.extend([
            financial_health.get("payment_history_score", 0),
            financial_health.get("contract_violations", 0),
            1 if financial_health.get("deposit_ready", False) else 0
        ])
        
        market_fit_signals = business_data.get("market_fit_signals", {})
        values.extend([
            market_fit_signals.get("interest_from_mall_owners", 0),
            market_fit_signals.get("outreach_received_count", 0),
            market_fit_signals.get("offers_received", 0),
            market_fit_signals.get("negotiation_stage_count", 0)
        ])
        
        historical_track_record = business_data.get("historical_track_record", {})
        values.extend([
            historical_track_record.get("total_locations", 0),
            historical_track_record.get("successful_locations", 0),
            historical_track_record.get("avg_location_duration_months", 0)
        ])
        
        vector = np.array(values, dtype=float)
    else:
        vector = np.array(business_data, dtype=float) if business_data else np.array([])
    
    if len(vector) < expected_length:
        vector = np.pad(vector, (0, expected_length - len(vector)), 'constant')
    elif len(vector) > expected_length:
        vector = vector[:expected_length]
    
    return vector

def get_mall_vector(mall_record: dict):
    demographic_vec = normalize_demographic_vector(mall_record.get("demographic", {}))
    
    return {
        "avg_daily_visitors": mall_record.get("avg_daily_visitors", 0),
        "demographic_vec": demographic_vec
    }

def get_business_vector(biz_record: dict):
    target_demo_vec = normalize_business_vector(biz_record.get("target_demographic", {}))
    
    return {
        "budget": float(biz_record.get("budget") or 0),
        "required_size": float(biz_record.get("required_size") or 0),
        "visitor_capacity": biz_record.get("visitor_capacity", 0),
        "target_demo_vec": target_demo_vec
    }
```

app/model/models.py
```python
from sqlalchemy import Column, String, Integer, Float, Boolean, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Mall(Base):
    __tablename__ = "mall"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    type = Column(Text)
    avg_daily_visitors = Column(Integer)
    rent_price_usd = Column(Numeric(10, 2))
    management_fee_usd = Column(Numeric(10, 2))
    vat_percent = Column(Numeric(5, 2))
    motorbike_fee_vnd = Column(Numeric(12, 0))
    car_fee_vnd = Column(Numeric(12, 0))
    electricity_policy = Column(Text)
    overtime_fee_policy = Column(Text)
    lease_term = Column(Text)
    deposit_policy = Column(Text)
    payment_policy = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Zone(Base):
    __tablename__ = "zone"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Booth(Base):
    __tablename__ = "booth"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, index=True)
    size_m2 = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    floor_level = Column(Integer)
    zone = Column(String(10), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    brand_tier = Column(Text)
    budget = Column(Numeric)
    required_size = Column(Numeric)
    visitor_capacity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BusinessHistory(Base):
    __tablename__ = "business_history"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, index=True)
    revenue = Column(Numeric)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

app/model/cache_demographics.py
```python
from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from .models import Base, generate_uuid

class MallDemographics(Base):
    __tablename__ = "mall_demographics"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False, unique=True)
    spending_power = Column(JSON)
    visit_purpose = Column(JSON)
    traffic_pattern = Column(JSON)
    tenant_mix = Column(JSON)
    zone_performance = Column(JSON)
    historical_performance = Column(JSON)
    verified_data = Column(JSON)
    market_intelligence = Column(JSON)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BusinessDemographics(Base):
    __tablename__ = "business_demographics"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, unique=True)
    proven_performance = Column(JSON)
    historical_track_record = Column(JSON)
    requirements = Column(JSON)
    search_behavior = Column(JSON)
    business_profile = Column(JSON)
    financial_health = Column(JSON)
    market_fit_signals = Column(JSON)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

app/service/traffic.py
```python
from ..service.features import get_mall_vector, get_business_vector
from ..datastore.cache_manager import cache_recommendations, get_cached_recommendations
from sklearn.metrics.pairwise import cosine_similarity
from ..datastore.etl import run_etl
import numpy as np

def compute_match(mall, biz):
    mall_vec = get_mall_vector(mall)
    biz_vec = get_business_vector(biz)

    budget_fit = min(biz_vec["budget"] / 1_000_000, 1.0) if biz_vec["budget"] > 0 else 0.5
    
    traffic_fit = 0.5
    if mall_vec["avg_daily_visitors"] > 0 and biz_vec["visitor_capacity"] > 0:
        traffic_fit = min(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"]) / \
                      max(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"])

    demo_fit = 0.5
    if mall_vec["demographic_vec"].size > 0 and biz_vec["target_demo_vec"].size > 0:
        mall_demo = mall_vec["demographic_vec"].reshape(1, -1)
        biz_demo = biz_vec["target_demo_vec"].reshape(1, -1)
        
        if mall_demo.shape[1] == biz_demo.shape[1]:
            demo_fit = cosine_similarity(mall_demo, biz_demo)[0][0]
        else:
            demo_fit = 0.5

    score = 0.4 * budget_fit + 0.3 * traffic_fit + 0.3 * demo_fit
    return {
        "mall_id": mall["mall_id"],
        "business_id": biz["business_id"],
        "budget_fit": float(budget_fit),
        "traffic_fit": float(traffic_fit),
        "demo_fit": float(demo_fit),
        "score": float(score)
    }

def get_top_matches(limit: int = 10, use_cache: bool = True):
    cache_key = f"top_matches_{limit}"

    if use_cache:
        cached_results = get_cached_recommendations(cache_key)
        if cached_results:
            return cached_results
        
    malls, businesses = run_etl(use_cache=use_cache)

    matches = []
    for mall in malls:
        for biz in businesses:
            match = compute_match(mall, biz)
            matches.append(match)

    top_matches = sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]
    
    if use_cache:
        cache_recommendations(top_matches, cache_key, expire=1800)
    
    return top_matches

def get_matches_for_mall(mall_id: str, limit: int = 10, use_cache: bool = True):
    cache_key = f"mall_recommendations_{mall_id}_{limit}"
    
    if use_cache:
        cached_results = get_cached_recommendations(cache_key)
        if cached_results:
            return cached_results

    malls, businesses = run_etl(use_cache=use_cache)
    
    target_mall = None
    for mall in malls:
        if str(mall["mall_id"]) == mall_id:
            target_mall = mall
            break
    
    if not target_mall:
        raise ValueError(f"Mall with ID {mall_id} not found")
    
    matches = []
    for biz in businesses:
        match = compute_match(target_mall, biz)
        matches.append(match)
    
    top_matches = sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]
    
    if use_cache:
        cache_recommendations(top_matches, cache_key, expire=1800)
    
    return top_matches

def get_matches_for_business(business_id: str, limit: int = 10, use_cache: bool = True):
    cache_key = f"business_recommendations_{business_id}_{limit}"
    
    if use_cache:
        cached_results = get_cached_recommendations(cache_key)
        if cached_results:
            return cached_results

    malls, businesses = run_etl(use_cache=use_cache)
    
    target_business = None
    for biz in businesses:
        if str(biz["business_id"]) == business_id:
            target_business = biz
            break
    
    if not target_business:
        raise ValueError(f"Business with ID {business_id} not found")
    
    matches = []
    for mall in malls:
        match = compute_match(mall, target_business)
        matches.append(match)
    
    top_matches = sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]
    
    if use_cache:
        cache_recommendations(top_matches, cache_key, expire=1800)
    
    return top_matches
```

app/service/demographics_calculator.py
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.models import Mall, Booth, Business, BusinessHistory
from app.datastore.cache_manager import cache_mall_demographic, cache_business_data
from typing import Dict, Any

class DemographicsCalculator:
    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_mall_demographics(self, mall_id: str) -> Dict[str, Any]:
        mall = self.db.query(Mall).filter(Mall.id == mall_id).first()
        if not mall:
            return None

        booths = self.db.query(Booth).filter(Booth.mall_id == mall_id).all()
        business_histories = self.db.query(BusinessHistory).filter(BusinessHistory.mall_id == mall_id).all()

        total_booths = len(booths)
        occupied_booths = len([b for b in booths if not b.is_available])
        occupancy_rate = (occupied_booths / total_booths * 100) if total_booths > 0 else 0

        # Calculate zone statistics and demographics
        demographics = {
            "spending_power": {"budget": 30, "mid_range": 50, "premium": 20},
            "visit_purpose": {"shopping": 60, "dining": 25, "entertainment": 15},
            "traffic_pattern": {
                "weekday": 40, "weekend": 60,
                "peak_hours": [12, 13, 14, 18, 19, 20],
                "avg_dwell_time_minutes": 90
            },
            "tenant_mix": {
                "total_booths": total_booths,
                "occupied_booths": occupied_booths,
                "occupancy_rate": round(occupancy_rate, 2)
            },
            "historical_performance": {
                "total_businesses": len(business_histories),
                "successful_businesses": len([h for h in business_histories if h.success])
            },
            "verified_data": {
                "last_verification_date": "2024-10-06",
                "verification_status": "calculated"
            },
            "market_intelligence": {
                "avg_daily_visitors": mall.avg_daily_visitors or 0,
                "mall_type": mall.type or "unknown"
            }
        }
        return demographics

    def calculate_business_demographics(self, business_id: str) -> Dict[str, Any]:
        business = self.db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None

        business_histories = self.db.query(BusinessHistory).filter(BusinessHistory.business_id == business_id).all()

        demographics = {
            "proven_performance": {
                "avg_revenue": sum(h.revenue for h in business_histories if h.revenue) / len(business_histories) if business_histories else 0
            },
            "requirements": {
                "budget": float(business.budget) if business.budget else 0,
                "required_size": float(business.required_size) if business.required_size else 0
            },
            "business_profile": {
                "name": business.name,
                "category": business.category or "unknown"
            }
        }
        return demographics

    def cache_all_demographics(self):
        results = {"malls_processed": 0, "businesses_processed": 0, "errors": []}

        malls = self.db.query(Mall).all()
        for mall in malls:
            try:
                demographics = self.calculate_mall_demographics(mall.id)
                if demographics:
                    cache_mall_demographic(mall.id, demographics, expire=3600)
                    results["malls_processed"] += 1
            except Exception as e:
                results["errors"].append(f"Mall {mall.id}: {str(e)}")

        businesses = self.db.query(Business).all()
        for business in businesses:
            try:
                demographics = self.calculate_business_demographics(business.id)
                if demographics:
                    cache_business_data(business.id, demographics, expire=3600)
                    results["businesses_processed"] += 1
            except Exception as e:
                results["errors"].append(f"Business {business.id}: {str(e)}")

        return results
```

app/rest/api.py
```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict
from ..service.traffic import get_top_matches, get_matches_for_mall, get_matches_for_business

app = FastAPI(
    title="Mall-Business Recommendation API",
    description="API for matching malls with businesses based on demographics, traffic, and budget",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Mall-Business Recommendation API", "status": "active"}

@app.get("/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=100, description="Number of top recommendations to return"),
    use_cache: bool = Query(default=True, description="Whether to use cached data")
):
    try:
        recommendations = get_top_matches(limit=limit, use_cache=use_cache)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(recommendations),
                "recommendations": recommendations
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/cache/demographics")
async def cache_demographics():
    try:
        from ..config.db import get_db
        from ..service.demographics_calculator import DemographicsCalculator
        
        db_gen = get_db()
        db = next(db_gen)
        try:
            calculator = DemographicsCalculator(db)
            results = calculator.cache_all_demographics()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Demographics calculation and caching completed",
                    "results": results
                }
            )
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error caching demographics: {str(e)}")
```

app/server.py
```python
import uvicorn
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def startup_checks():
    from app.config.redis import startup_redis_check
    
    if not startup_redis_check():
        print("Redis connection failed - service may not work properly")
        return False

    print("All startup checks passed")
    return True

if __name__ == "__main__":
    startup_checks()

    port = int(os.getenv("PORT", 8000))

    print(f"Starting server at http://0.0.0.0:{port}")
    uvicorn.run(
        "app.rest.api:app",
        host="0.0.0.0", 
        port=port,
        reload=True,
        log_level="info"
    )
```