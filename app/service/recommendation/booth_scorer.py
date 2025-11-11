from typing import Any, Dict, List, Tuple


class BoothScorer:
    def __init__(self, brand: Dict[str, Any], booth: Dict[str, Any], mall_score: float):
        self.brand = brand
        self.booth = booth
        self.mall_score = mall_score

    def score_financial(self) -> Tuple[int, List[str]]:
        explanations = []
        fp = self.brand.get("financial_performance", {})
        fc = self.brand.get("financial_capacity", {})
        op = self.brand.get("operational_profile", {})

        max_aff_rent = fc.get("max_affordable_rent", 0)
        comfort_range = fc.get("comfortable_rent_range", [0, 0])
        income_stability = fp.get("income_stability_score", 0)
        space_required = op.get("space_requirement_m2", 0)

        booth_price = self.booth.get("rent_price")
        if booth_price is None:
            booth_size = self.booth.get("size_m2", 0)
            if booth_size > 0 and space_required > 0:
                estimated_price_per_sqm = 1000000
                booth_price = booth_size * estimated_price_per_sqm
                explanations.append(f"No booth price available. Using estimated price based on size: {booth_price}")
            else:
                explanations.append(
                    "No booth price available and cannot estimate. Financial scoring may be inaccurate."
                )
                booth_price = 0

        explanations.append(f"Booth rent price: {booth_price}")

        if booth_price <= comfort_range[0]:
            score = 30
            explanations.append("Rent is well within comfortable budget range.")
        elif booth_price <= comfort_range[1]:
            score = 25
            explanations.append("Rent is within upper comfortable range.")
        elif booth_price <= max_aff_rent:
            score = 15
            explanations.append("Rent is affordable but tight.")
        else:
            score = 5
            explanations.append("Rent is above the maximum affordable (over budget).")

        if income_stability >= 8:
            score += 5
            explanations.append("High income stability. Bonus points added.")
        elif income_stability >= 6:
            score += 3
            explanations.append("Moderate income stability. Some bonus points added.")
        else:
            explanations.append("Low income stability. No stability bonus.")

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

    def score_physical(self) -> Tuple[int, List[str]]:
        explanations = []
        op = self.brand.get("operational_profile", {})
        req = self.brand.get("requirements", {})

        space_required = op.get("space_requirement_m2", 0)
        booth_size = self.booth.get("size_m2")

        score = 0

        if space_required > 0 and booth_size:
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
            explanations.append("Size requirement not specified or booth size unknown.")

        frontage_pref = req.get("preferred_frontage_width")
        booth_frontage = self.booth.get("frontage_width_m")
        if frontage_pref and booth_frontage:
            if booth_frontage >= frontage_pref:
                score += 5
                explanations.append(f"Frontage width {booth_frontage}m meets or exceeds preference {frontage_pref}m.")
            else:
                score += 2
                explanations.append(f"Frontage width {booth_frontage}m is below preference {frontage_pref}m.")
        else:
            explanations.append("No frontage preference or booth frontage unknown.")

        ceiling_pref = req.get("preferred_ceiling_height")
        booth_ceiling = self.booth.get("ceiling_height_m")
        if ceiling_pref and booth_ceiling:
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
            if booth_shape.lower() == shape_pref.lower():
                score += 2
                explanations.append(f"Booth shape {booth_shape} matches preference.")
            else:
                explanations.append(f"Booth shape {booth_shape} does not match preference {shape_pref}.")
        else:
            explanations.append("No shape preference or booth shape unknown.")

        return min(score, 25), explanations

    def score_mall_inheritance(self) -> Tuple[int, List[str]]:
        explanations = []
        mall_score_normalized = (self.mall_score / 100.0) * 15
        score = int(mall_score_normalized)
        explanations.append(f"Inherited {score} points from mall compatibility score ({self.mall_score:.2f}).")
        return min(score, 15), explanations

    def compute_final_score(self) -> Dict[str, Any]:
        comp_scores = {}
        explanations = {}
        total = 0

        comp, expl = self.score_financial()
        comp_scores["financial"] = comp
        explanations["financial"] = expl
        total += comp

        comp, expl = self.score_location()
        comp_scores["location"] = comp
        explanations["location"] = expl
        total += comp

        comp, expl = self.score_physical()
        comp_scores["physical"] = comp
        explanations["physical"] = expl
        total += comp

        comp, expl = self.score_mall_inheritance()
        comp_scores["mall_inheritance"] = comp
        explanations["mall_inheritance"] = expl
        total += comp

        booth_score = (total / 100) * 100

        composite_score = (self.mall_score * 0.4) + (booth_score * 0.6)

        return {
            "booth_score": round(booth_score, 2),
            "mall_score": round(self.mall_score, 2),
            "composite_score": round(composite_score, 2),
            "component_scores": comp_scores,
            "explanations": explanations,
        }
