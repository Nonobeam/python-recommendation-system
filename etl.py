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
