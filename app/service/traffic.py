import sys
from pathlib import Path

app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from service.features import get_mall_vector, get_business_vector
from datastore.cache_manager import cache_recommendations, get_cached_recommendations
from sklearn.metrics.pairwise import cosine_similarity
from datastore.etl import run_etl
import numpy as np


def calculate_budget_fit(mall_vec, biz_vec):
    """Calculate budget compatibility between mall and business"""
    return min(biz_vec["budget"] / 1_000_000, 1.0) if biz_vec["budget"] > 0 else 0.5


def calculate_traffic_fit(mall_vec, biz_vec):
    """Calculate traffic compatibility between mall and business"""
    traffic_fit = 0.5
    if mall_vec["avg_daily_visitors"] > 0 and biz_vec["visitor_capacity"] > 0:
        traffic_fit = min(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"]) / \
                      max(mall_vec["avg_daily_visitors"], biz_vec["visitor_capacity"])
    return traffic_fit


def calculate_demographic_fit(mall_vec, biz_vec):
    """Calculate demographic compatibility using cosine similarity"""
    demo_fit = 0.5
    if mall_vec["demographic_vec"].size > 0 and biz_vec["target_demo_vec"].size > 0:
        mall_demo = mall_vec["demographic_vec"].reshape(1, -1)
        biz_demo = biz_vec["target_demo_vec"].reshape(1, -1)
        
        if mall_demo.shape[1] == biz_demo.shape[1]:
            demo_fit = cosine_similarity(mall_demo, biz_demo)[0][0]
        else:
            demo_fit = 0.5
    return demo_fit


def calculate_zone_compatibility(zone_data, biz):
    """Calculate how well business fits in a specific zone"""
    biz_requirements = biz.get('target_demographic', {}).get('requirements', {})
    
    min_traffic = biz_requirements.get('min_traffic_needed', 0)
    zone_traffic = zone_data.get('avg_traffic_per_day', 0)
    traffic_match = min(zone_traffic / max(min_traffic, 1), 1.0) if min_traffic > 0 else 0.5
    
    biz_budget = biz_requirements.get('budget', 0)
    zone_avg_price = zone_data.get('avg_revenue_per_booth', 0)
    if biz_budget > 0 and zone_avg_price > 0:
        budget_match = 1.0 - abs(biz_budget - zone_avg_price) / max(biz_budget, zone_avg_price)
        budget_match = max(0, budget_match)
    else:
        budget_match = 0.5
    
    zone_occupancy = zone_data.get('occupancy_rate', 0) / 100
    occupancy_score = 1.0 - abs(zone_occupancy - 0.85)
    
    return 0.4 * traffic_match + 0.4 * budget_match + 0.2 * occupancy_score


def calculate_historical_fit(mall, biz):
    """Score based on business's past success in similar malls"""
    biz_history = biz.get('target_demographic', {}).get('historical_track_record', {})
    mall_type = mall.get('type', '')
    
    best_performing_type = biz_history.get('best_performing_mall_type', '')
    type_match = 1.0 if best_performing_type.lower() == mall_type.lower() else 0.5
    
    total_locations = biz_history.get('total_locations', 0)
    successful_locations = biz_history.get('successful_locations', 0)
    success_rate = successful_locations / max(total_locations, 1) if total_locations > 0 else 0.5
    
    avg_duration = biz_history.get('avg_location_duration_months', 12)
    stability_score = min(avg_duration / 24, 1.0)
    
    return 0.4 * type_match + 0.3 * success_rate + 0.3 * stability_score


def calculate_tenant_mix_fit(mall, biz):
    """Ensure business fits tenant mix without over-saturation"""
    tenant_mix = mall.get('demographic', {}).get('tenant_mix', {})
    biz_category = biz.get('category', '')
    
    shop_pct = tenant_mix.get('shop_percent', 0)
    food_pct = tenant_mix.get('food_percent', 0)
    service_pct = tenant_mix.get('service_percent', 0)
    
    category_map = {
        'restaurant': 'food',
        'cafe': 'food',
        'retail': 'shop',
        'clothing': 'shop',
        'service': 'service'
    }
    biz_type = category_map.get(biz_category.lower(), 'shop')
    
    if biz_type == 'food':
        score = 1.0 - (food_pct / 100) if food_pct < 40 else 0.3
    elif biz_type == 'service':
        score = 1.0 - (service_pct / 100) if service_pct < 20 else 0.3
    else:
        score = 1.0 - (shop_pct / 100) if shop_pct < 70 else 0.5
    
    return max(0, score)


def calculate_market_interest_boost(biz):
    """Boost score if business has received interest from malls"""
    signals = biz.get('target_demographic', {}).get('market_fit_signals', {})
    
    interest_count = signals.get('interest_from_mall_owners', 0)
    outreach_count = signals.get('outreach_received_count', 0)
    offers_count = signals.get('offers_received', 0)
    
    interest_score = min((interest_count * 0.02 + 
                         outreach_count * 0.01 + 
                         offers_count * 0.05), 0.2)
    
    return interest_score


def compute_match(mall, biz):
    """Enhanced rule-based matching with multiple factors"""
    mall_vec = get_mall_vector(mall)
    biz_vec = get_business_vector(biz)

    budget_fit = calculate_budget_fit(mall_vec, biz_vec)
    traffic_fit = calculate_traffic_fit(mall_vec, biz_vec)
    demo_fit = calculate_demographic_fit(mall_vec, biz_vec)
    
    historical_fit = calculate_historical_fit(mall, biz)
    tenant_mix_fit = calculate_tenant_mix_fit(mall, biz)
    market_boost = calculate_market_interest_boost(biz)
    
    base_score = (0.25 * budget_fit + 
                  0.20 * traffic_fit + 
                  0.20 * demo_fit +
                  0.20 * historical_fit +
                  0.15 * tenant_mix_fit)
    
    final_score = base_score * (1 + market_boost)
    
    return {
        "mall_id": mall["mall_id"],
        "business_id": biz["business_id"],
        "budget_fit": float(budget_fit),
        "traffic_fit": float(traffic_fit),
        "demo_fit": float(demo_fit),
        "historical_fit": float(historical_fit),
        "tenant_mix_fit": float(tenant_mix_fit),
        "market_boost": float(market_boost),
        "score": float(min(final_score, 1.0))
    }


def compute_match_with_zones(mall, biz):
    """Match business to best zone within mall"""
    mall_vec = get_mall_vector(mall)
    biz_vec = get_business_vector(biz)
    
    budget_fit = calculate_budget_fit(mall_vec, biz_vec)
    traffic_fit = calculate_traffic_fit(mall_vec, biz_vec)
    demo_fit = calculate_demographic_fit(mall_vec, biz_vec)
    
    zone_scores = {}
    zone_performance = mall.get('demographic', {}).get('zone_performance', {})
    
    for zone_name, zone_data in zone_performance.items():
        zone_score = calculate_zone_compatibility(zone_data, biz)
        zone_scores[zone_name] = zone_score
    
    best_zone = max(zone_scores.items(), key=lambda x: x[1]) if zone_scores else None
    zone_fit = best_zone[1] if best_zone else 0.5
    
    score = (0.3 * budget_fit + 
             0.25 * traffic_fit + 
             0.25 * demo_fit + 
             0.2 * zone_fit)
    
    return {
        "mall_id": mall["mall_id"],
        "business_id": biz["business_id"],
        "budget_fit": float(budget_fit),
        "traffic_fit": float(traffic_fit),
        "demo_fit": float(demo_fit),
        "zone_fit": float(zone_fit),
        "recommended_zone": best_zone[0] if best_zone else None,
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