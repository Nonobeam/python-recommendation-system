from typing import Any, Dict, List, Tuple


class BusinessMatchScorer:
    def __init__(self, brand: Dict[str, Any], mall: Dict[str, Any]):
        self.brand = brand
        self.mall = mall

    def score_financial(self) -> Tuple[int, List[str]]:
        explanations = []
        fp = self.brand.get("financial_performance", {})
        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})
        pc = self.mall.get("pricing_context", {})

        max_aff_rent = fc.get("max_affordable_rent", 0)
        comfort_range = fc.get("comfortable_rent_range", [0, 0])
        income_stability = fp.get("income_stability_score", 0)
        space_required = op.get("space_requirement_m2", 0)
        avg_rent_per_sqm = pc.get("avg_rent_per_sqm", 0)

        estimated_rent = space_required * avg_rent_per_sqm
        explanations.append(f"Estimated rent: {estimated_rent}")

        if estimated_rent <= comfort_range[0]:
            score = 30
            explanations.append("Rent is well within comfortable budget range.")
        elif estimated_rent <= comfort_range[1]:
            score = 25
            explanations.append("Rent is within upper comfortable range.")
        elif estimated_rent <= max_aff_rent:
            score = 15
            explanations.append("Rent is affordable but tight.")
        else:
            score = 5
            explanations.append("Rent is above the maximum affordable (over budget).")

        # Step 3: Adjust for income stability
        if income_stability >= 8:
            score += 5
            explanations.append("High income stability. Bonus points added.")
        elif income_stability >= 6:
            score += 3
            explanations.append("Moderate income stability. Some bonus points added.")
        else:
            explanations.append("Low income stability. No stability bonus.")

        return min(score, 35), explanations

    def score_tenant_mix(self) -> Tuple[int, List[str]]:
        explanations = []
        op = self.brand.get("operational_profile", {})
        req = self.brand.get("requirements", {})
        te = self.mall.get("tenant_ecosystem", {})
        cat = (op.get("category") or "").lower()
        target_zones = set(req.get("target_zones", []))
        available_zones = set(self.mall.get("zone_performance", {}).keys())

        if "restaurant" in cat or "cafe" in cat:
            category_percent = te.get("food_percent", 0)
            explanations.append(f"Category = food. Mall food_percent = {category_percent}%.")
        elif "retail" in cat or "clothing" in cat:
            category_percent = te.get("shop_percent", 0)
            explanations.append(f"Category = retail. Mall shop_percent = {category_percent}%.")
        elif "service" in cat:
            category_percent = te.get("service_percent", 0)
            explanations.append(f"Category = service. Mall service_percent = {category_percent}%.")
        else:
            category_percent = 0
            explanations.append("Unknown or other category. No oversaturation penalty.")

        if category_percent < 25:
            score = 25
            explanations.append("Category is under-represented. Excellent tenant mix.")
        elif category_percent < 40:
            score = 20
            explanations.append("Category is balanced.")
        elif category_percent < 55:
            score = 12
            explanations.append("Category getting crowded.")
        elif category_percent < 70:
            score = 5
            explanations.append("Category somewhat oversaturated.")
        else:
            score = 0
            explanations.append("Category oversaturated.")

        # Step 3: zone preferences
        if target_zones & available_zones:
            score += 5
            explanations.append("Brand's target zone matches available booth zones.")
        else:
            explanations.append("No match between brand's target zones and available zones.")

        return min(score, 30), explanations

    def score_market_position(self) -> Tuple[int, List[str]]:
        explanations = []
        op = self.brand.get("operational_profile", {})
        req = self.brand.get("requirements", {})
        vp = self.mall.get("visitor_profile", {})
        te = self.mall.get("tenant_ecosystem", {})
        mp = self.mall.get("market_position", {})
        spending_dist = vp.get("spending_power_distribution", {})
        mall_type = mp.get("mall_type", "")
        brand_cat = (op.get("category") or "").lower()
        pm_types = set(req.get("preferred_mall_types", []))
        occupancy_rate = te.get("occupancy_rate", 0)
        # Match spending power
        pct = 0
        if "luxury" in brand_cat or "premium" in brand_cat:
            pct = spending_dist.get("premium", 0) * 0.4
            explanations.append(f"Brand is premium/luxury. Mall premium percent = {spending_dist.get('premium', 0)}%.")
        elif "mid" in brand_cat:
            pct = spending_dist.get("mid_range", 0) * 0.4
            explanations.append(f"Brand is mid-range. Mall mid_range percent = {spending_dist.get('mid_range', 0)}%.")
        elif "budget" in brand_cat:
            pct = spending_dist.get("budget", 0) * 0.4
            explanations.append(f"Brand is budget. Mall budget percent = {spending_dist.get('budget', 0)}%.")
        else:
            explanations.append("Brand category not premium/mid/budget; spending power not scored.")
        score = int(pct)
        # Mall type preference
        if mall_type in pm_types:
            score += 10
            explanations.append("Mall type matches preferred types.")
        else:
            score += 5
            explanations.append("Mall type not preferred, neutral score.")
        # Occupancy bonus
        if occupancy_rate > 85:
            score += 5
            explanations.append("Mall is healthy (>85% occupancy).")
        elif occupancy_rate > 70:
            score += 3
            explanations.append("Mall is stable (>70% occupancy).")
        elif occupancy_rate > 50:
            score += 1
            explanations.append("Mall occupancy moderate (>50%).")
        else:
            score -= 2
            explanations.append("Mall struggling (<50% occupancy). Penalty applied.")
        return min(score, 20), explanations

    def score_operational(self) -> Tuple[int, List[str]]:
        explanations = []
        req = self.brand.get("requirements", {})
        op = self.brand.get("operational_profile", {})
        facilities = set(req.get("required_facilities", []))
        # booth/mall facilities simulated as mall-level here
        available = set(self.mall.get("facilities", []))
        facilities_matched = len(facilities & available)
        score = 0
        if facilities:
            score = int((facilities_matched / len(facilities)) * 10)
            explanations.append(f"Matched {facilities_matched} / {len(facilities)} required facilities.")
        else:
            explanations.append("No facilities requirements provided.")
        # Operating hours compatibility
        brand_hours = op.get("operating_hours", "")
        peak_hours = self.mall.get("visitor_profile", {}).get("peak_hours", [])
        # crude matching: does brand_hours overlap any peak_hours?
        overlap = False
        if brand_hours and peak_hours:
            try:
                b_start, b_end = [int(t.replace(":", "")) for t in brand_hours.split("-")]
                for hour in peak_hours:
                    hour_val = hour * 100  # 12 => 1200
                    if b_start <= hour_val <= b_end:
                        overlap = True
                        break
            except Exception:
                pass
        if overlap:
            score += 5
            explanations.append("Brand's operating hours overlap mall peak hours. Full points.")
        else:
            score += 2
            explanations.append("No peak hour overlap or info; partial points.")
        return min(score, 15), explanations

    def score_location(self) -> Tuple[int, List[str]]:
        explanations = []
        mp = self.mall.get("market_position", {})
        loc_dist = mp.get("location_distance", "")
        acc_score = mp.get("accessibility_score", 0)
        base = 0
        km = None
        if isinstance(loc_dist, (int, float)):
            km = float(loc_dist)
        else:
            try:
                if loc_dist.endswith("km"):
                    km = float(loc_dist.replace("km", ""))
            except Exception:
                pass
        if km is not None:
            if km <= 5:
                base = 10
                explanations.append("Mall is within 5km: excellent proximity.")
            elif km <= 10:
                base = 7
                explanations.append("Mall within 10km: good distance.")
            elif km <= 20:
                base = 4
                explanations.append("Mall within 20km: fair distance.")
            else:
                base = 1
                explanations.append("Mall is far (>20km): poor location.")
        else:
            explanations.append("Unknown location distance. No proximity points.")
        # accessibility bonus
        if acc_score >= 8:
            base += 3
            explanations.append("High accessibility score. +3 points.")
        elif acc_score >= 6:
            base += 2
            explanations.append("Moderate accessibility score. +2 points.")
        else:
            explanations.append("Low accessibility; no bonus.")
        return min(base, 13), explanations

    def compute_final_score(self) -> Dict[str, Any]:
        comp_scores = {}
        explanations = {}
        total = 0
        comp, expl = self.score_financial()
        comp_scores["financial"] = comp
        explanations["financial"] = expl
        total += comp
        comp, expl = self.score_tenant_mix()
        comp_scores["tenant_mix"] = comp
        explanations["tenant_mix"] = expl
        total += comp
        comp, expl = self.score_market_position()
        comp_scores["market_position"] = comp
        explanations["market_position"] = expl
        total += comp
        comp, expl = self.score_operational()
        comp_scores["operational"] = comp
        explanations["operational"] = expl
        total += comp
        comp, expl = self.score_location()
        comp_scores["location"] = comp
        explanations["location"] = expl
        total += comp
        # Normalization
        final_score = (total / 113) * 100
        # --- Penalties & Bonuses ---
        # Critical Penalties
        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})
        pc = self.mall.get("pricing_context", {})
        te = self.mall.get("tenant_ecosystem", {})
        tsm = self.mall.get("tenant_success_metrics", {})
        estimated_rent = op.get("space_requirement_m2", 0) * pc.get("avg_rent_per_sqm", 0)
        if estimated_rent > fc.get("max_affordable_rent", 0):
            final_score *= 0.7
        if te.get("occupancy_rate", 100) < 40:
            final_score *= 0.8
        if max(te.get("shop_percent", 0), te.get("food_percent", 0), te.get("service_percent", 0)) > 70:
            final_score *= 0.85
        # Success bonuses
        if tsm.get("tenant_turnover_rate", 100) < 10:
            final_score *= 1.1
        if tsm.get("renewal_rate", 0) > 70:
            final_score *= 1.05
        final_score = max(0, min(round(final_score, 2), 100))
        return {"final_score": final_score, "component_scores": comp_scores, "explanations": explanations}
