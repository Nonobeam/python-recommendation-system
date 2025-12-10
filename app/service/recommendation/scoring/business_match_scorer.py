from typing import Any, Dict, List, Optional, Tuple

from .score_calculator import apply_mall_adjustments, normalize_score
from .scoring_utils import safe_get_number


class BusinessMatchScorer:
    """
    Calculates brand-mall compatibility scores using a rule-based framework.

    Scoring Dimensions (0-100 scale):
    1. Financial Compatibility (35 points max)
    2. Tenant Mix & Category Fit (30 points max)
    3. Market Position & Demographics (20 points max)
    4. Operational Compatibility (15 points max)
    5. Location & Accessibility (13 points max)

    See RECOMMENDATION_SCORING_FRAMEWORK.md for detailed documentation.
    """

    def __init__(self, brand: Dict[str, Any], mall: Dict[str, Any]):
        self.brand = brand
        self.mall = mall

    def score_financial(self) -> Tuple[Optional[int], List[str]]:
        """
        Score financial compatibility (0-35 points).

        Evaluates rent affordability and income stability.
        Returns: (score, explanations)
        """
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

        score = 0
        has_valid_comparison = False

        if space_required is not None and avg_rent_per_sqm is not None:
            estimated_rent = space_required * avg_rent_per_sqm
            explanations.append(f"Estimated rent: {estimated_rent}")

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
        else:
            if space_required is None:
                explanations.append("Cannot calculate estimated rent: space_requirement_m2 is missing from brand.")
            if avg_rent_per_sqm is None:
                explanations.append("Cannot calculate estimated rent: avg_rent_per_sqm is missing from mall.")

            if max_aff_rent is not None and avg_rent_per_sqm is not None:
                has_valid_comparison = True
                avg_price_context = avg_rent_per_sqm * 50
                explanations.append(f"Using mall avg_rent_per_sqm ({avg_rent_per_sqm}) as price indicator.")
                if avg_price_context <= max_aff_rent:
                    score = 15
                    explanations.append("Mall pricing appears affordable based on avg rent per sqm.")
                else:
                    score = 5
                    explanations.append("Mall pricing may be high based on avg rent per sqm.")

        if income_stability is not None:
            has_valid_comparison = True
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

        if not has_valid_comparison:
            return None, explanations

        return min(score, 35), explanations

    def score_tenant_mix(self) -> Tuple[Optional[int], List[str]]:
        """
        Score tenant mix and category fit (0-30 points).

        Evaluates category oversaturation to avoid crowded categories.
        Returns: (score, explanations)
        """
        explanations = []
        op = self.brand.get("operational_profile", {})
        te = self.mall.get("tenant_ecosystem", {})
        cat = (op.get("category") or "").lower()

        category_percent = None
        if "restaurant" in cat or "cafe" in cat or "food" in cat or "giải trí" in cat:
            category_percent = safe_get_number(te, "food_percent")
            if category_percent is not None:
                explanations.append(f"Category = food/entertainment. Mall food_percent = {category_percent}%.")
        elif "retail" in cat or "clothing" in cat or "shop" in cat:
            category_percent = safe_get_number(te, "shop_percent")
            if category_percent is not None:
                explanations.append(f"Category = retail. Mall shop_percent = {category_percent}%.")
        elif "service" in cat or "dịch vụ" in cat:
            category_percent = safe_get_number(te, "service_percent")
            if category_percent is not None:
                explanations.append(f"Category = service. Mall service_percent = {category_percent}%.")
        else:
            explanations.append(f"Category '{cat}' not explicitly matched. Applying neutral score.")

        score = 0
        has_valid_score = False

        if category_percent is not None:
            has_valid_score = True
            if category_percent < 25:
                score = 25
                explanations.append("Category is under-represented. Excellent tenant mix opportunity.")
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
                score = 15
                has_valid_score = True
                explanations.append(
                    f"Category '{cat}' identified but mall percentage data missing. Neutral score applied."
                )
            else:
                score = 10
                has_valid_score = True
                explanations.append("Category not specified. Minimal baseline score applied.")

        if not has_valid_score:
            score = 10
            has_valid_score = True
            explanations.append("Minimal baseline score applied due to insufficient tenant mix data.")

        return min(score, 30), explanations

    def score_market_position(self) -> Tuple[Optional[int], List[str]]:
        """
        Score market position and demographics (0-20 points).

        Evaluates occupancy health and competition level using demographics data.
        Returns: (score, explanations)
        """
        explanations = []
        te = self.mall.get("tenant_ecosystem", {})
        mp = self.mall.get("market_position", {})
        occupancy_rate = safe_get_number(te, "occupancy_rate")
        competition_nearby = safe_get_number(mp, "competition_nearby")

        score = 0
        has_valid_score = False

        # Occupancy scoring (0-15 pts)
        if occupancy_rate is not None:
            has_valid_score = True
            if occupancy_rate > 85:
                score += 15
                explanations.append("Mall is healthy (>85% occupancy).")
            elif occupancy_rate > 70:
                score += 12
                explanations.append("Mall is stable (>70% occupancy).")
            elif occupancy_rate > 50:
                score += 8
                explanations.append("Mall occupancy moderate (>50%).")
            elif occupancy_rate >= 0:
                score += 4
                explanations.append(f"Mall has low occupancy ({occupancy_rate}%). Minimal score.")
            else:
                score = 0
                explanations.append("Mall struggling with negative indicators.")
        else:
            score = 8
            has_valid_score = True
            explanations.append("Occupancy rate missing. Baseline score applied.")

        # Competition scoring (0-5 pts)
        if competition_nearby is not None:
            has_valid_score = True
            if competition_nearby == 0:
                score += 5
                explanations.append("Unique location - no nearby competition. +5 points.")
            elif competition_nearby == 1:
                score += 4
                explanations.append("Low competition (1 nearby mall). +4 points.")
            elif competition_nearby <= 3:
                score += 2
                explanations.append(f"Moderate competition ({competition_nearby} nearby malls). +2 points.")
            elif competition_nearby <= 5:
                score += 0
                explanations.append(f"High competition ({competition_nearby} nearby malls). No bonus.")
            else:
                score -= 2
                explanations.append(f"Very high competition ({competition_nearby} nearby malls). -2 penalty.")
        else:
            explanations.append("Competition data missing. No competition adjustment.")

        if not has_valid_score:
            score = 10
            has_valid_score = True
            explanations.append("Minimal baseline score applied due to insufficient data.")

        return min(score, 20), explanations

    def score_operational(self) -> Tuple[Optional[int], List[str]]:
        """
        Score operational compatibility (0-15 points).

        Returns baseline score (no facility matching without requirements data).
        Returns: (score, explanations)
        """
        explanations = []
        score = 10
        explanations.append("Operational baseline score applied (facility matching not available).")
        return min(score, 15), explanations

    def score_location(self) -> Tuple[Optional[int], List[str]]:
        """
        Score location and accessibility (0-13 points).

        Evaluates accessibility features from demographics only.
        Returns: (score, explanations)
        """
        explanations = []
        mp = self.mall.get("market_position", {})
        acc_score = safe_get_number(mp, "accessibility_score")
        base = 5  # Default baseline
        has_valid_score = False

        if acc_score is not None:
            has_valid_score = True
            if acc_score >= 8:
                base = 13
                explanations.append("High accessibility score (>=8). Excellent location.")
            elif acc_score >= 6:
                base = 10
                explanations.append("Moderate accessibility score (>=6). Good location.")
            elif acc_score >= 4:
                base = 7
                explanations.append("Fair accessibility score (>=4). Adequate location.")
            elif acc_score > 0:
                base = 4
                explanations.append("Low accessibility score. Limited location advantages.")
            else:
                base = 2
                explanations.append("No accessibility features. Poor location.")
        else:
            base = 7
            has_valid_score = True
            explanations.append("Accessibility score missing. Neutral baseline applied.")

        if not has_valid_score:
            base = 7
            has_valid_score = True
            explanations.append("Minimal baseline location score applied.")

        return min(base, 13), explanations

    def compute_final_score(self) -> Dict[str, Any]:
        """
        Compute final compatibility score (0-100).

        Aggregates all component scores, normalizes to 0-100 scale,
        and applies adjustment factors (penalties/bonuses).

        Returns:
            Dictionary with final_score, component_scores, and explanations
        """
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

        base_score = normalize_score(total, max_possible_score)
        final_score = apply_mall_adjustments(base_score, self.brand, self.mall)
        return {"final_score": final_score, "component_scores": comp_scores, "explanations": explanations}
