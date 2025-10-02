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
