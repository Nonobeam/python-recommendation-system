from typing import Any, Dict, List, Optional, Tuple

from .scoring_utils import is_valid_number, safe_get_number


class BusinessMatchScorer:
    def __init__(self, brand: Dict[str, Any], mall: Dict[str, Any]):
        self.brand = brand
        self.mall = mall

    def score_financial(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        fp = self.brand.get("financial_performance", {})
        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})
        pc = self.mall.get("pricing_context", {})

        max_aff_rent = safe_get_number(fc, "max_affordable_rent")
        comfort_range = fc.get("comfortable_rent_range")
        income_stability = safe_get_number(fp, "income_stability_score")
        space_required = safe_get_number(op, "space_requirement_m2")
        avg_rent_per_sqm = safe_get_number(pc, "avg_rent_per_sqm")

        if comfort_range is None or not isinstance(comfort_range, list) or len(comfort_range) < 2:
            comfort_range = [None, None]
        else:
            comfort_range = [
                safe_get_number({"val": comfort_range[0]}, "val") if len(comfort_range) > 0 else None,
                safe_get_number({"val": comfort_range[1]}, "val") if len(comfort_range) > 1 else None,
            ]

        if space_required is None or avg_rent_per_sqm is None:
            if space_required is None and avg_rent_per_sqm is None:
                explanations.append("Cannot calculate estimated rent: space_required and avg_rent_per_sqm are missing.")
                return None, explanations
            explanations.append("Cannot calculate estimated rent: missing required values.")
            return None, explanations

        estimated_rent = space_required * avg_rent_per_sqm
        explanations.append(f"Estimated rent: {estimated_rent}")

        score = 0
        has_valid_comparison = False

        if comfort_range[0] is not None and comfort_range[1] is not None:
            has_valid_comparison = True
            if estimated_rent <= comfort_range[0]:
                score = 30
                explanations.append("Rent is well within comfortable budget range.")
            elif estimated_rent <= comfort_range[1]:
                score = 25
                explanations.append("Rent is within upper comfortable range.")
            elif max_aff_rent is not None and estimated_rent <= max_aff_rent:
                score = 15
                explanations.append("Rent is affordable but tight.")
            elif max_aff_rent is not None:
                score = 5
                explanations.append("Rent is above the maximum affordable (over budget).")
            else:
                score = 10
                explanations.append("Rent calculated but max_affordable_rent missing. Partial score.")
        elif max_aff_rent is not None:
            has_valid_comparison = True
            if estimated_rent <= max_aff_rent:
                score = 20
                explanations.append("Rent is within affordable range (comfortable range missing).")
            else:
                score = 5
                explanations.append("Rent is above the maximum affordable (over budget).")
        else:
            explanations.append("Cannot compare rent: max_affordable_rent and comfortable_rent_range are missing.")

        if not has_valid_comparison:
            return None, explanations

        if income_stability is not None:
            if income_stability >= 8:
                score += 5
                explanations.append("High income stability. Bonus points added.")
            elif income_stability >= 6:
                score += 3
                explanations.append("Moderate income stability. Some bonus points added.")
            else:
                explanations.append("Low income stability. No stability bonus.")
        else:
            explanations.append("Income stability score missing. No stability bonus.")

        return min(score, 35), explanations

    def score_tenant_mix(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        op = self.brand.get("operational_profile", {})
        req = self.brand.get("requirements", {})
        te = self.mall.get("tenant_ecosystem", {})
        cat = (op.get("category") or "").lower()
        target_zones = set(req.get("target_zones", []))
        available_zones = set(self.mall.get("zone_performance", {}).keys())

        category_percent = None
        if "restaurant" in cat or "cafe" in cat:
            category_percent = safe_get_number(te, "food_percent")
            if category_percent is not None:
                explanations.append(f"Category = food. Mall food_percent = {category_percent}%.")
        elif "retail" in cat or "clothing" in cat:
            category_percent = safe_get_number(te, "shop_percent")
            if category_percent is not None:
                explanations.append(f"Category = retail. Mall shop_percent = {category_percent}%.")
        elif "service" in cat:
            category_percent = safe_get_number(te, "service_percent")
            if category_percent is not None:
                explanations.append(f"Category = service. Mall service_percent = {category_percent}%.")
        else:
            explanations.append("Unknown or other category. No oversaturation penalty.")

        score = 0
        has_valid_score = False

        if category_percent is not None:
            has_valid_score = True
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
        else:
            if cat:
                explanations.append("Category identified but percentage data missing. No category score.")
            else:
                explanations.append("Category not specified. No category score.")

        if target_zones and available_zones:
            if target_zones & available_zones:
                score += 5
                explanations.append("Brand's target zone matches available booth zones.")
            else:
                explanations.append("No match between brand's target zones and available zones.")
        else:
            explanations.append("Zone preferences or available zones missing. No zone match score.")

        if not has_valid_score and not (target_zones and available_zones):
            return None, explanations

        return min(score, 30), explanations

    def score_market_position(self) -> Tuple[Optional[int], List[str]]:
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
        occupancy_rate = safe_get_number(te, "occupancy_rate")

        score = 0
        has_valid_score = False

        if spending_dist:
            premium_pct = safe_get_number(spending_dist, "premium")
            mid_pct = safe_get_number(spending_dist, "mid_range")
            budget_pct = safe_get_number(spending_dist, "budget")

            if "luxury" in brand_cat or "premium" in brand_cat:
                if premium_pct is not None:
                    pct = premium_pct * 0.4
                    score = int(pct)
                    has_valid_score = True
                    explanations.append(f"Brand is premium/luxury. Mall premium percent = {premium_pct}%.")
                else:
                    explanations.append("Brand is premium/luxury but premium percent missing.")
            elif "mid" in brand_cat:
                if mid_pct is not None:
                    pct = mid_pct * 0.4
                    score = int(pct)
                    has_valid_score = True
                    explanations.append(f"Brand is mid-range. Mall mid_range percent = {mid_pct}%.")
                else:
                    explanations.append("Brand is mid-range but mid_range percent missing.")
            elif "budget" in brand_cat:
                if budget_pct is not None:
                    pct = budget_pct * 0.4
                    score = int(pct)
                    has_valid_score = True
                    explanations.append(f"Brand is budget. Mall budget percent = {budget_pct}%.")
                else:
                    explanations.append("Brand is budget but budget percent missing.")
            else:
                explanations.append("Brand category not premium/mid/budget; spending power not scored.")
        else:
            explanations.append("Spending power distribution missing.")

        if mall_type:
            if pm_types and mall_type in pm_types:
                score += 10
                has_valid_score = True
                explanations.append("Mall type matches preferred types.")
            else:
                score += 5
                has_valid_score = True
                explanations.append("Mall type not preferred, neutral score.")
        else:
            explanations.append("Mall type missing. No mall type score.")

        if occupancy_rate is not None:
            has_valid_score = True
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
        else:
            explanations.append("Occupancy rate missing. No occupancy bonus.")

        if not has_valid_score:
            return None, explanations

        return min(score, 20), explanations

    def score_operational(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        req = self.brand.get("requirements", {})
        op = self.brand.get("operational_profile", {})
        facilities = set(req.get("required_facilities", []))
        available = set(self.mall.get("facilities", []))
        facilities_matched = len(facilities & available)
        score = 0
        has_valid_score = False

        if facilities:
            has_valid_score = True
            score = int((facilities_matched / len(facilities)) * 10)
            explanations.append(f"Matched {facilities_matched} / {len(facilities)} required facilities.")
        else:
            explanations.append("No facilities requirements provided.")

        brand_hours = op.get("operating_hours", "")
        peak_hours = self.mall.get("visitor_profile", {}).get("peak_hours", [])
        overlap = False
        if brand_hours and peak_hours:
            try:
                b_start, b_end = [int(t.replace(":", "")) for t in brand_hours.split("-")]
                for hour in peak_hours:
                    if is_valid_number(hour):
                        hour_val = int(hour) * 100
                        if b_start <= hour_val <= b_end:
                            overlap = True
                            break
            except Exception:
                pass

        if overlap:
            has_valid_score = True
            score += 5
            explanations.append("Brand's operating hours overlap mall peak hours. Full points.")
        elif brand_hours or peak_hours:
            has_valid_score = True
            score += 2
            explanations.append("No peak hour overlap or info; partial points.")
        else:
            explanations.append("Operating hours and peak hours missing. No hours score.")

        if not has_valid_score:
            return None, explanations

        return min(score, 15), explanations

    def score_location(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        mp = self.mall.get("market_position", {})
        loc_dist = mp.get("location_distance", "")
        acc_score = safe_get_number(mp, "accessibility_score")
        base = 0
        has_valid_score = False

        km = None
        if isinstance(loc_dist, (int, float)):
            if is_valid_number(loc_dist):
                km = float(loc_dist)
        elif isinstance(loc_dist, str):
            try:
                if loc_dist.endswith("km"):
                    km_val = float(loc_dist.replace("km", "").strip())
                    if is_valid_number(km_val):
                        km = km_val
            except Exception:
                pass

        if km is not None:
            has_valid_score = True
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

        if acc_score is not None:
            has_valid_score = True
            if acc_score >= 8:
                base += 3
                explanations.append("High accessibility score. +3 points.")
            elif acc_score >= 6:
                base += 2
                explanations.append("Moderate accessibility score. +2 points.")
            else:
                explanations.append("Low accessibility; no bonus.")
        else:
            explanations.append("Accessibility score missing. No accessibility bonus.")

        if not has_valid_score:
            return None, explanations

        return min(base, 13), explanations

    def compute_final_score(self) -> Dict[str, Any]:
        comp_scores = {}
        explanations = {}
        total = 0
        valid_components = 0
        max_possible_score = 0

        comp, expl = self.score_financial()
        comp_scores["financial"] = comp
        explanations["financial"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 35

        comp, expl = self.score_tenant_mix()
        comp_scores["tenant_mix"] = comp
        explanations["tenant_mix"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 30

        comp, expl = self.score_market_position()
        comp_scores["market_position"] = comp
        explanations["market_position"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 20

        comp, expl = self.score_operational()
        comp_scores["operational"] = comp
        explanations["operational"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 15

        comp, expl = self.score_location()
        comp_scores["location"] = comp
        explanations["location"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 13

        if valid_components == 0:
            return {
                "final_score": float("nan"),
                "component_scores": comp_scores,
                "explanations": explanations,
            }

        if max_possible_score == 0:
            return {
                "final_score": float("nan"),
                "component_scores": comp_scores,
                "explanations": explanations,
            }

        final_score = (total / max_possible_score) * 100

        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})
        pc = self.mall.get("pricing_context", {})
        te = self.mall.get("tenant_ecosystem", {})
        tsm = self.mall.get("tenant_success_metrics", {})

        space_required = safe_get_number(op, "space_requirement_m2")
        avg_rent_per_sqm = safe_get_number(pc, "avg_rent_per_sqm")
        max_aff_rent = safe_get_number(fc, "max_affordable_rent")

        if space_required is not None and avg_rent_per_sqm is not None and max_aff_rent is not None:
            estimated_rent = space_required * avg_rent_per_sqm
            if estimated_rent > max_aff_rent:
                final_score *= 0.7

        occupancy_rate = safe_get_number(te, "occupancy_rate")
        if occupancy_rate is not None and occupancy_rate < 40:
            final_score *= 0.8

        shop_pct = safe_get_number(te, "shop_percent")
        food_pct = safe_get_number(te, "food_percent")
        service_pct = safe_get_number(te, "service_percent")
        if shop_pct is not None or food_pct is not None or service_pct is not None:
            max_pct = max(
                shop_pct if shop_pct is not None else 0,
                food_pct if food_pct is not None else 0,
                service_pct if service_pct is not None else 0,
            )
            if max_pct > 70:
                final_score *= 0.85

        turnover_rate = safe_get_number(tsm, "tenant_turnover_rate")
        if turnover_rate is not None and turnover_rate < 10:
            final_score *= 1.1

        renewal_rate = safe_get_number(tsm, "renewal_rate")
        if renewal_rate is not None and renewal_rate > 70:
            final_score *= 1.05

        final_score = max(0, min(round(final_score, 2), 100))
        return {"final_score": final_score, "component_scores": comp_scores, "explanations": explanations}
