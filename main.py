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