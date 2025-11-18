from typing import Any, Dict, List, Optional, Tuple

from .score_calculator import calculate_composite_score, normalize_score
from .scoring_utils import is_valid_number, safe_get_number


class BoothScorer:
    def __init__(self, brand: Dict[str, Any], booth: Dict[str, Any], mall_score: float):
        self.brand = brand
        self.booth = booth
        self.mall_score = mall_score

    def score_financial(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        fp = self.brand.get("financial_performance", {})
        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})

        max_aff_rent = safe_get_number(fc, "max_affordable_rent")
        comfort_range = fc.get("comfortable_rent_range")
        income_stability = safe_get_number(fp, "income_stability_score")
        space_required = safe_get_number(op, "space_requirement_m2")

        if comfort_range is None or not isinstance(comfort_range, list) or len(comfort_range) < 2:
            comfort_range = [None, None]
        else:
            comfort_range = [
                safe_get_number({"val": comfort_range[0]}, "val") if len(comfort_range) > 0 else None,
                safe_get_number({"val": comfort_range[1]}, "val") if len(comfort_range) > 1 else None,
            ]

        booth_price = safe_get_number(self.booth, "rent_price")
        if booth_price is None:
            booth_size = safe_get_number(self.booth, "size_m2")
            if booth_size is not None and space_required is not None and booth_size > 0 and space_required > 0:
                estimated_price_per_sqm = 1000000
                booth_price = booth_size * estimated_price_per_sqm
                explanations.append(f"No booth price available. Using estimated price based on size: {booth_price}")
            else:
                explanations.append(
                    "No booth price available and cannot estimate. Financial scoring may be inaccurate."
                )
                if booth_price is None:
                    return None, explanations

        explanations.append(f"Booth rent price: {booth_price}")

        score = 0
        has_valid_comparison = False

        if comfort_range[0] is not None and comfort_range[1] is not None:
            has_valid_comparison = True
            if booth_price <= comfort_range[0]:
                score = 30
                explanations.append("Rent is well within comfortable budget range.")
            elif booth_price <= comfort_range[1]:
                score = 25
                explanations.append("Rent is within upper comfortable range.")
            elif max_aff_rent is not None and booth_price <= max_aff_rent:
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
            if booth_price <= max_aff_rent:
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

    def score_location(self) -> Tuple[int, List[str]]:
        explanations = []
        req = self.brand.get("requirements", {})

        preferred_floors = req.get("preferred_floors", [])
        booth_floor = self.booth.get("floor_level")

        score = 0

        if preferred_floors and booth_floor is not None:
            if booth_floor in preferred_floors:
                score += 10
                explanations.append(f"Floor level {booth_floor} matches preferred floors.")
            else:
                score += 5
                explanations.append(f"Floor level {booth_floor} does not match preferred floors.")
        else:
            score += 5
            explanations.append("No floor preference specified or booth floor unknown.")

        required_facilities = set(req.get("required_facilities", []))
        booth_facilities = set()

        if self.booth.get("has_electricity"):
            booth_facilities.add("electricity")
        if self.booth.get("has_water_supply"):
            booth_facilities.add("water")
        if self.booth.get("has_ventilation"):
            booth_facilities.add("ventilation")
        if self.booth.get("has_drainage"):
            booth_facilities.add("drainage")
        if self.booth.get("has_gas_line"):
            booth_facilities.add("gas")
        if self.booth.get("has_internet"):
            booth_facilities.add("internet")

        if required_facilities:
            facilities_matched = len(required_facilities & booth_facilities)
            facility_score = int((facilities_matched / len(required_facilities)) * 10)
            score += facility_score
            explanations.append(f"Matched {facilities_matched} / {len(required_facilities)} required facilities.")
        else:
            score += 5
            explanations.append("No facilities requirements specified.")

        zone_id = self.booth.get("zone_id")
        target_zones = set(req.get("target_zones", []))
        if target_zones and zone_id:
            if zone_id in target_zones:
                score += 5
                explanations.append("Booth zone matches target zones.")
            else:
                explanations.append("Booth zone does not match target zones.")
        else:
            explanations.append("No zone preference or booth zone unknown.")

        return min(score, 25), explanations

    def score_physical(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        op = self.brand.get("operational_profile", {})
        req = self.brand.get("requirements", {})

        space_required = safe_get_number(op, "space_requirement_m2")
        booth_size = safe_get_number(self.booth, "size_m2")

        score = 0
        has_valid_score = False

        if space_required is not None and booth_size is not None and space_required > 0:
            has_valid_score = True
            size_diff = abs(booth_size - space_required) / space_required
            if size_diff <= 0.1:
                score += 15
                explanations.append(f"Booth size {booth_size}m² closely matches required {space_required}m².")
            elif size_diff <= 0.2:
                score += 10
                explanations.append(f"Booth size {booth_size}m² is within 20% of required {space_required}m².")
            elif size_diff <= 0.3:
                score += 5
                explanations.append(f"Booth size {booth_size}m² is within 30% of required {space_required}m².")
            else:
                explanations.append(
                    f"Booth size {booth_size}m² differs significantly from required {space_required}m²."
                )
        else:
            score += 5
            has_valid_score = True
            explanations.append("Size requirement not specified or booth size unknown.")

        frontage_pref = safe_get_number(req, "preferred_frontage_width")
        booth_frontage = safe_get_number(self.booth, "frontage_width_m")
        if frontage_pref is not None and booth_frontage is not None:
            has_valid_score = True
            if booth_frontage >= frontage_pref:
                score += 5
                explanations.append(f"Frontage width {booth_frontage}m meets or exceeds preference {frontage_pref}m.")
            else:
                score += 2
                explanations.append(f"Frontage width {booth_frontage}m is below preference {frontage_pref}m.")
        else:
            explanations.append("No frontage preference or booth frontage unknown.")

        ceiling_pref = safe_get_number(req, "preferred_ceiling_height")
        booth_ceiling = safe_get_number(self.booth, "ceiling_height_m")
        if ceiling_pref is not None and booth_ceiling is not None:
            has_valid_score = True
            if booth_ceiling >= ceiling_pref:
                score += 3
                explanations.append(f"Ceiling height {booth_ceiling}m meets or exceeds preference {ceiling_pref}m.")
            else:
                score += 1
                explanations.append(f"Ceiling height {booth_ceiling}m is below preference {ceiling_pref}m.")
        else:
            explanations.append("No ceiling height preference or booth ceiling unknown.")

        shape_pref = req.get("preferred_shape")
        booth_shape = self.booth.get("shape")
        if shape_pref and booth_shape:
            has_valid_score = True
            if booth_shape.lower() == shape_pref.lower():
                score += 2
                explanations.append(f"Booth shape {booth_shape} matches preference.")
            else:
                explanations.append(f"Booth shape {booth_shape} does not match preference {shape_pref}.")
        else:
            explanations.append("No shape preference or booth shape unknown.")

        if not has_valid_score:
            return None, explanations

        return min(score, 25), explanations

    def score_mall_inheritance(self) -> Tuple[Optional[int], List[str]]:
        explanations = []
        if not is_valid_number(self.mall_score):
            explanations.append("Mall score is invalid (None or NaN). No inheritance score.")
            return None, explanations
        mall_score_normalized = (self.mall_score / 100.0) * 15
        score = int(mall_score_normalized)
        explanations.append(f"Inherited {score} points from mall compatibility score ({self.mall_score:.2f}).")
        return min(score, 15), explanations

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

        comp, expl = self.score_location()
        comp_scores["location"] = comp
        explanations["location"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 25

        comp, expl = self.score_physical()
        comp_scores["physical"] = comp
        explanations["physical"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 25

        comp, expl = self.score_mall_inheritance()
        comp_scores["mall_inheritance"] = comp
        explanations["mall_inheritance"] = expl
        if comp is not None:
            total += comp
            valid_components += 1
            max_possible_score += 15

        if valid_components == 0:
            return {
                "booth_score": float("nan"),
                "mall_score": round(self.mall_score, 2) if is_valid_number(self.mall_score) else float("nan"),
                "composite_score": float("nan"),
                "component_scores": comp_scores,
                "explanations": explanations,
            }

        if max_possible_score == 0:
            return {
                "booth_score": float("nan"),
                "mall_score": round(self.mall_score, 2) if is_valid_number(self.mall_score) else float("nan"),
                "composite_score": float("nan"),
                "component_scores": comp_scores,
                "explanations": explanations,
            }

        booth_score = normalize_score(total, max_possible_score)
        composite_score = calculate_composite_score(self.mall_score, booth_score)

        return {
            "booth_score": round(booth_score, 2),
            "mall_score": round(self.mall_score, 2) if is_valid_number(self.mall_score) else float("nan"),
            "composite_score": round(composite_score, 2) if is_valid_number(composite_score) else float("nan"),
            "component_scores": comp_scores,
            "explanations": explanations,
        }
