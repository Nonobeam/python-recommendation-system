import pandas as pd

from app.config.db import SessionLocal
from app.datastore.cache_manager import (clear_data_cache, get_cache_status,
                                         get_cached_business_data,
                                         get_cached_mall_demographic)
from app.exception import BusinessDataError, DemographicDataError
from app.model.models import Business, Mall
from app.utils.logger import etl_logger


def extract_mall_data():
    etl_logger.info("Fetching mall data from database")
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        data = []

        for m in malls:
            mall_id = str(m.id)

            cached_demographic = get_cached_mall_demographic(mall_id)

            if not cached_demographic:
                raise DemographicDataError(mall_id, "mall")

            demographic = cached_demographic

            data.append(
                {
                    "mall_id": m.id,
                    "name": m.name,
                    "type": m.type,
                    "avg_daily_visitors": m.avg_daily_visitors,
                    "demographic": demographic,
                }
            )

        return pd.DataFrame(data)


def extract_business_data():
    etl_logger.info("Fetching business data from database")
    with SessionLocal() as session:
        businesses = session.query(Business).all()
        data = []

        for b in businesses:
            business_id = str(b.id)

            cached_business_data = get_cached_business_data(business_id)

            if not cached_business_data:
                raise BusinessDataError(business_id)

            data.append(
                {
                    "business_id": b.id,
                    "name": b.name,
                    "category": b.category,
                    "brand_tier": b.brand_tier,
                    "budget": b.budget,
                    "required_size": b.required_size,
                    "visitor_capacity": b.visitor_capacity,
                    "target_demographic": cached_business_data,
                }
            )

        return pd.DataFrame(data)


def transform_mall(data: pd.DataFrame):
    return data[["mall_id", "name", "type", "avg_daily_visitors", "demographic"]]


def transform_business(data: pd.DataFrame):
    return data[
        [
            "business_id",
            "name",
            "category",
            "brand_tier",
            "budget",
            "required_size",
            "visitor_capacity",
            "target_demographic",
        ]
    ]


def load(data: pd.DataFrame):
    return data.to_dict(orient="records")


def run_etl(use_cache: bool = True):
    """
    Run ETL pipeline with optional caching
    Args:
        use_cache: Whether to use cached data if available
    """
    if not use_cache:
        etl_logger.info("Running ETL without cache")
        clear_data_cache()

    # Show cache status
    cache_status = get_cache_status()
    etl_logger.debug(f"Cache status: {cache_status}")

    malls_raw = extract_mall_data()
    businesses_raw = extract_business_data()
    malls = transform_mall(malls_raw)
    businesses = transform_business(businesses_raw)
    return load(malls), load(businesses)
