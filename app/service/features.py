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
