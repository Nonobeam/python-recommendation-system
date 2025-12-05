from typing import Any, Dict, Optional

from .scoring_utils import is_valid_number, safe_get_number


def normalize_score(total: float, max_possible_score: float) -> float:
    """
    Normalize a score to a 0-100 scale based on maximum possible score.

    Args:
        total: Sum of all component scores
        max_possible_score: Maximum possible score if all components were perfect

    Returns:
        Normalized score (0-100), or NaN if max_possible_score is 0
    """
    if max_possible_score == 0:
        return float("nan")
    return (total / max_possible_score) * 100


def apply_mall_adjustments(
    base_score: float,
    brand: Dict[str, Any],
    mall: Dict[str, Any],
) -> float:
    """
    Apply adjustment factors to a mall compatibility score based on business rules.

    Applies three penalty multipliers:
    - Over Budget Penalty: If estimated_rent > max_affordable_rent: score × 0.7
    - Low Occupancy Penalty: If occupancy_rate < 40%: score × 0.8
    - Oversaturation Penalty: If any category > 70%: score × 0.85

    Args:
        base_score: Base score before adjustments (0-100)
        brand: Brand data dictionary
        mall: Mall data dictionary

    Returns:
        Adjusted score (0-100), clamped between 0 and 100

    Note:
        Tenant success metrics (turnover/renewal bonuses) have been removed.
    """
    if not is_valid_number(base_score):
        return base_score

    adjusted_score = base_score

    fc = brand.get("financial_capacity", {})
    op = brand.get("operational_profile", {})
    pc = mall.get("pricing_context", {})
    te = mall.get("tenant_ecosystem", {})

    space_required = safe_get_number(op, "space_requirement_m2")
    avg_rent_per_sqm = safe_get_number(pc, "avg_rent_per_sqm")
    max_aff_rent = safe_get_number(fc, "max_affordable_rent")

    if space_required is not None and avg_rent_per_sqm is not None and max_aff_rent is not None:
        estimated_rent = space_required * avg_rent_per_sqm
        if estimated_rent > max_aff_rent:
            adjusted_score *= 0.7

    occupancy_rate = safe_get_number(te, "occupancy_rate")
    if occupancy_rate is not None and occupancy_rate < 40:
        adjusted_score *= 0.8

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
            adjusted_score *= 0.85

    return max(0, min(round(adjusted_score, 2), 100))


def calculate_composite_score(
    mall_score: float, booth_score: float, mall_weight: float = 0.4, booth_weight: float = 0.6
) -> float:
    """
    Calculate composite score from mall and booth scores.

    Args:
        mall_score: Mall compatibility score (0-100)
        booth_score: Booth compatibility score (0-100)
        mall_weight: Weight for mall score (default: 0.4)
        booth_weight: Weight for booth score (default: 0.6)

    Returns:
        Composite score (0-100), or NaN if either score is invalid
    """
    if not is_valid_number(mall_score) or not is_valid_number(booth_score):
        return float("nan")
    composite = (mall_score * mall_weight) + (booth_score * booth_weight)
    return round(composite, 2)


def calculate_brand_recommendation_score(
    mall_score: float,
    booth_score: Optional[float],
    available_booths_count: int,
) -> float:
    """
    Calculate final brand recommendation score for a mall.

    Args:
        mall_score: Mall compatibility score (0-100)
        booth_score: Best booth match score (0-100) or None
        available_booths_count: Number of available booths in the mall

    Returns:
        Final recommendation score (0-100)
    """
    if not is_valid_number(mall_score):
        return float("nan")

    if booth_score is not None and is_valid_number(booth_score) and booth_score > 0:
        final_score = (mall_score * 0.6) + (booth_score * 0.4)
    else:
        if available_booths_count > 0:
            final_score = mall_score * 0.7
        else:
            final_score = mall_score * 0.5

    return min(round(final_score, 2), 100.0)
