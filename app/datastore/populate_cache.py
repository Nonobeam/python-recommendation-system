from ..config.redis import cache
from ..config.db import SessionLocal
from ..model.models import Mall, Business
import os

DEMOGRAPHIC_PREFIX = os.getenv("REDIS_CACHE_DEMOGRAPHIC_KEY_PREFIX", "mall_demographic_")
BUSINESS_PREFIX = os.getenv("REDIS_CACHE_BUSINESS_KEY_PREFIX", "mall_business_")

def populate_sample_demographic_data():
    """Populate Redis with sample demographic data for testing"""
    
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        businesses = session.query(Business).all()
        
        print(f"Found {len(malls)} malls and {len(businesses)} businesses in database")
        
        mall_count = 0
        for mall in malls:
            mall_id = str(mall.id)
            
            sample_demographic = {
                "spending_power": {
                    "budget": 30,
                    "mid_range": 50,
                    "premium": 20
                },
                "visit_purpose": {
                    "shopping": 60,
                    "dining": 25,
                    "entertainment": 15
                },
                "traffic_pattern": {
                    "weekday": 40,
                    "weekend": 60
                },
                "dwell_time_avg_minutes": 90
            }
            
            cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
            success = cache.set(cache_key, sample_demographic, expire=86400)  # 24 hours
            
            if success:
                mall_count += 1
                print(f"✓ Cached demographic for mall {mall_id}")
            else:
                print(f"✗ Failed to cache demographic for mall {mall_id}")
        
        business_count = 0
        for business in businesses:
            business_id = str(business.id)
            
            sample_business_data = {
                "spending_power": {
                    "budget": 10,
                    "mid_range": 70,
                    "premium": 20
                },
                "visit_purpose": {
                    "shopping": 80,
                    "dining": 10,
                    "entertainment": 10
                },
                "traffic_pattern": {
                    "weekday": 30,
                    "weekend": 70
                },
                "required_dwell_time_minutes": 45
            }
            
            cache_key = f"{BUSINESS_PREFIX}{business_id}"
            success = cache.set(cache_key, sample_business_data, expire=86400)  # 24 hours
            
            if success:
                business_count += 1
                print(f"✓ Cached business data for business {business_id}")
            else:
                print(f"✗ Failed to cache business data for business {business_id}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Malls processed: {mall_count}/{len(malls)}")
        print(f"Businesses processed: {business_count}/{len(businesses)}")
        
        return {"malls": mall_count, "businesses": business_count}

def validate_demographic_format(data, data_type="mall"):
    """Validate if demographic data has the correct format"""
    required_fields = ["spending_power", "visit_purpose", "traffic_pattern"]
    
    if data_type == "mall":
        required_fields.append("dwell_time_avg_minutes")
    else:  # business
        required_fields.append("required_dwell_time_minutes")
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    if "spending_power" in data:
        sp = data["spending_power"]
        if not all(key in sp for key in ["budget", "mid_range", "premium"]):
            return False, "spending_power missing required keys"
    
    if "visit_purpose" in data:
        vp = data["visit_purpose"]
        if not all(key in vp for key in ["shopping", "dining", "entertainment"]):
            return False, "visit_purpose missing required keys"
    
    if "traffic_pattern" in data:
        tp = data["traffic_pattern"]
        if not all(key in tp for key in ["weekday", "weekend"]):
            return False, "traffic_pattern missing required keys"
    
    return True, "Valid format"

def check_and_init_cache():
    """Check if cache exists with correct format, initialize if needed"""
    
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        businesses = session.query(Business).all()
        
        malls_need_init = []
        businesses_need_init = []
        
        print("=== CHECKING CACHE FORMAT ===")
        
        for mall in malls:
            mall_id = str(mall.id)
            cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
            cached_data = cache.get(cache_key)
            
            if not cached_data:
                malls_need_init.append(mall_id)
                print(f"✗ Mall {mall_id}: No cache found")
            else:
                is_valid, message = validate_demographic_format(cached_data, "mall")
                if not is_valid:
                    malls_need_init.append(mall_id)
                    print(f"✗ Mall {mall_id}: Invalid format - {message}")
                else:
                    print(f"✓ Mall {mall_id}: Valid format")
        
        for business in businesses:
            business_id = str(business.id)
            cache_key = f"{BUSINESS_PREFIX}{business_id}"
            cached_data = cache.get(cache_key)
            
            if not cached_data:
                businesses_need_init.append(business_id)
                print(f"✗ Business {business_id}: No cache found")
            else:
                is_valid, message = validate_demographic_format(cached_data, "business")
                if not is_valid:
                    businesses_need_init.append(business_id)
                    print(f"✗ Business {business_id}: Invalid format - {message}")
                else:
                    print(f"✓ Business {business_id}: Valid format")
        
        if malls_need_init or businesses_need_init:
            print(f"\n=== INITIALIZING CACHE ===")
            print(f"Malls needing initialization: {len(malls_need_init)}")
            print(f"Businesses needing initialization: {len(businesses_need_init)}")
            
            populate_sample_demographic_data()
            return {"initialized": True, "malls": len(malls_need_init), "businesses": len(businesses_need_init)}
        else:
            print(f"\n✓ All cache entries have correct format")
            return {"initialized": False, "message": "All cache entries valid"}

def check_demographic_cache_coverage():
    """Check how many entities have demographic data in cache"""
    
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        businesses = session.query(Business).all()
        
        cached_malls = 0
        cached_businesses = 0
        
        print("=== CHECKING CACHE COVERAGE ===")
        
        for mall in malls:
            mall_id = str(mall.id)
            cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
            if cache.exists(cache_key):
                cached_malls += 1
            else:
                print(f"✗ Missing demographic cache for mall {mall_id}")
        
        for business in businesses:
            business_id = str(business.id)
            cache_key = f"{BUSINESS_PREFIX}{business_id}"
            if cache.exists(cache_key):
                cached_businesses += 1
            else:
                print(f"✗ Missing business cache for business {business_id}")
        
        print(f"\n=== COVERAGE SUMMARY ===")
        print(f"Malls with demographics: {cached_malls}/{len(malls)} ({cached_malls/len(malls)*100:.1f}%)")
        print(f"Businesses with data: {cached_businesses}/{len(businesses)} ({cached_businesses/len(businesses)*100:.1f}%)")
        
        return {
            "malls": {"cached": cached_malls, "total": len(malls)},
            "businesses": {"cached": cached_businesses, "total": len(businesses)}
        }

def clear_demographic_cache():
    """Clear all demographic cache entries"""
    
    with SessionLocal() as session:
        malls = session.query(Mall).all()
        businesses = session.query(Business).all()
        
        cleared_count = 0
        
        for mall in malls:
            mall_id = str(mall.id)
            cache_key = f"{DEMOGRAPHIC_PREFIX}{mall_id}"
            if cache.delete(cache_key):
                cleared_count += 1
        
        for business in businesses:
            business_id = str(business.id)
            cache_key = f"{BUSINESS_PREFIX}{business_id}"
            if cache.delete(cache_key):
                cleared_count += 1
        
        print(f"✓ Cleared {cleared_count} demographic cache entries")
        return cleared_count

if __name__ == "__main__":
    print("=== DEMOGRAPHIC CACHE UTILITY ===")
    print("1. Checking current cache coverage...")
    check_demographic_cache_coverage()
    
    print("\n2. Populating sample demographic data...")
    populate_sample_demographic_data()
    
    print("\n3. Verifying cache coverage after population...")
    check_demographic_cache_coverage()