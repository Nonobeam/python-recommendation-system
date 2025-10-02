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

👉 In short:
Phase 1 = Rule-based matching + ELK scoring → low cost, interpretable.
Phase 2 = Add ML recommender (collaborative + content-based).
Phase 3 = Optimize, expand features (traffic video analysis, dynamic pricing, feedback loops).

Current state
✅ Phrase 2 (what you have now)

Data sources: Mall features (rent, traffic, demographics) + Business features (budget, target customers, etc.).

Math used:

Budget Fit → ratio (business budget / mall rent) → normalized.

Traffic Fit → cosine similarity between mall traffic vector & business traffic need.

Demographic Fit → cosine similarity between mall demographics & business target demographics.

Final score = weighted average of fits.

Nature: deterministic, rule-based scoring → gives you interpretable baseline matches.

🔜 Phrase 3 (how to move to AI/ML)

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

👉 In short:

Phrase 2 = handcrafted math.

Phrase 3 = learn weights + nonlinear patterns from data.

db.py
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://landmall:landmall@ip:port/landmall_db?options=-c%20search_path%3Dplatform-service"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

etl.py
import pandas as pd
from db import SessionLocal
from models import Mall, Business

def extract_mall_data():
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        data = [
            {
                "mall_id": m.id,
                "name": m.name,
                "type": m.type,
                "avg_daily_visitors": m.avg_daily_visitors,
                "demographic": m.demographic,
            }
            for m in malls
        ]
        return pd.DataFrame(data)

def extract_business_data():
    with SessionLocal() as session:
        businesses = session.query(Business).all()
        data = [
            {
                "business_id": b.id,
                "name": b.name,
                "category": b.category,
                "brand_tier": b.brand_tier,
                "budget": b.budget,
                "required_size": b.required_size,
                "visitor_capacity": b.visitor_capacity,
                "target_demographic": b.target_demographic,
            }
            for b in businesses
        ]
        return pd.DataFrame(data)

def transform_mall(data: pd.DataFrame):
    return data[["mall_id", "name", "type", "avg_daily_visitors", "demographic"]]

def transform_business(data: pd.DataFrame):
    return data[["business_id", "name", "category", "brand_tier",
                 "budget", "required_size", "visitor_capacity", "target_demographic"]]

def load(data: pd.DataFrame):
    return data.to_dict(orient="records")

def run_etl():
    malls_raw = extract_mall_data()
    businesses_raw = extract_business_data()
    malls = transform_mall(malls_raw)
    businesses = transform_business(businesses_raw)
    return load(malls), load(businesses)


features.py
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

def json_to_vec(jsonb):
    if not jsonb:
        return np.array([])
    
    vec = []
    for v in jsonb.values():
        if isinstance(v, (int, float)):
            vec.append(v)
        elif isinstance(v, dict):
            for nested in v.values():
                if isinstance(nested, (int, float)):
                    vec.append(nested)
        else:
            try:
                vec.append(float(v))
            except:
                continue
    return np.array(vec, dtype=float)

def get_mall_vector(mall_record: dict):
    return {
        "avg_daily_visitors": mall_record.get("avg_daily_visitors", 0),
        "demographic_vec": json_to_vec(mall_record.get("demographic"))
    }

def get_business_vector(biz_record: dict):
    return {
        "budget": float(biz_record.get("budget") or 0),
        "required_size": float(biz_record.get("required_size") or 0),
        "visitor_capacity": biz_record.get("visitor_capacity", 0),
        "target_demo_vec": json_to_vec(biz_record.get("target_demographic"))
    }


models.py
from sqlalchemy import Column, String, Integer, Float, Boolean, Numeric, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class Mall(Base):
    __tablename__ = "mall"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    type = Column(String)
    avg_daily_visitors = Column(Integer)
    demographic = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Booth(Base):
    __tablename__ = "booth"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False)
    size_m2 = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    floor_level = Column(Integer)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    brand_tier = Column(String)
    budget = Column(Numeric)
    required_size = Column(Numeric)
    visitor_capacity = Column(Integer)
    target_demographic = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BusinessHistory(Base):
    __tablename__ = "business_history"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    business_id = Column(String, ForeignKey("business.id", ondelete="CASCADE"), nullable=False)
    mall_id = Column(String, ForeignKey("mall.id", ondelete="CASCADE"), nullable=False)
    revenue = Column(Numeric)
    success = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


main.py
from etl import run_etl
from features import get_mall_vector, get_business_vector
from sklearn.metrics.pairwise import cosine_similarity

def compute_match(mall, biz):
    mall_vec = get_mall_vector(mall)
    biz_vec = get_business_vector(biz)

    budget_fit = min(biz_vec["budget"] / 1_000_000, 1.0)  # normalize roughly
    traffic_fit = min(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"]) / \
                  max(1, max(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"]))

    demo_fit = 0
    if mall_vec["demographic_vec"].size > 0 and biz_vec["target_demo_vec"].size > 0:
        demo_fit = cosine_similarity(
            [mall_vec["demographic_vec"]],
            [biz_vec["target_demo_vec"]]
        )[0][0]

    score = 0.4 * budget_fit + 0.3 * traffic_fit + 0.3 * demo_fit

    return {
        "mall_id": mall["mall_id"],
        "business_id": biz["business_id"],
        "budget_fit": budget_fit,
        "traffic_fit": traffic_fit,
        "demo_fit": demo_fit,
        "score": score
    }

def main():
    malls, businesses = run_etl()

    matches = []
    for mall in malls:
        for biz in businesses:
            matches.append(compute_match(mall, biz))

    matches = sorted(matches, key=lambda x: x["score"], reverse=True)

    print("=== TOP MATCHES ===")
    for m in matches[:10]:
        print(m)

if __name__ == "__main__":
    main()