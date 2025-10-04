from ..service.features import get_mall_vector, get_business_vector
from ..datastore.cache_manager import cache_recommendations, get_cached_recommendations
from sklearn.metrics.pairwise import cosine_similarity
from ..datastore.etl import run_etl


def compute_match(mall, biz):
    mall_vec = get_mall_vector(mall)
    biz_vec = get_business_vector(biz)

    budget_fit = min(biz_vec["budget"] / 1_000_000, 1.0)
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