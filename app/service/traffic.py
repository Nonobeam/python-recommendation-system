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
    
    top_matches = sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]
    
    if use_cache:
        cache_recommendations(top_matches, cache_key, expire=1800)
    
    return top_matches