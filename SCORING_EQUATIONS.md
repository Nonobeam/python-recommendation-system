# Recommendation Scoring Equations

**Version**: 2.0 (Updated 2025-12-10)  
**Total Score Range**: 0-113 points → Normalized to 0-100

This document details the mathematical formulas and logic used to calculate brand-mall compatibility scores.

---

## Overview

The recommendation system evaluates 5 key dimensions:

1. **Financial Compatibility** (35 pts) - Can the brand afford this location?
2. **Tenant Mix** (30 pts) - Is there room for this category?
3. **Market Position** (20 pts) - Is the mall healthy and competitive?
4. **Operational** (15 pts) - Baseline compatibility
5. **Location & Accessibility** (13 pts) - Is the mall well-connected?

---

## 1. Financial Compatibility (35 points)

### Estimated Rent Calculation

```python
estimated_rent = avg_rent_per_sqm × space_requirement_m2
```

**Example**: 150,000 VND/m² × 50 m² = 7,500,000 VND/month

### A. Comfortable Range Check (20 points)

```python
if comfortable_rent_range[0] ≤ estimated_rent ≤ comfortable_rent_range[1]:
    score = 20  # Within comfort zone
elif estimated_rent ≤ max_affordable_rent:
    score = 10  # Affordable but tight
else:
    score = 0   # Too expensive
```

**Comfortable Range**: 20-30% of brand's monthly income

### B. Max Affordable Check (10 points)

```python
if estimated_rent ≤ max_affordable_rent:
    score = 10  # Brand can afford it
else:
    score = 0   # Over budget
```

**Max Affordable**: 30% of brand's monthly income (industry standard)

### C. Income Stability Bonus (5 points)

```python
if income_stability_score ≥ 8.0:
    score = 5   # Very stable income
elif income_stability_score ≥ 6.0:
    score = 3   # Moderate stability
elif income_stability_score ≥ 4.0:
    score = 1   # Some stability
else:
    score = 0   # Unstable income
```

**Income Stability Score**: 0-10 scale based on income variance over time

### Demographics Fields
- `mall.pricing_context.avg_rent_per_sqm`
- `brand.operational_profile.space_requirement_m2`
- `brand.financial_capacity.max_affordable_rent`
- `brand.financial_capacity.comfortable_rent_range`
- `brand.financial_performance.income_stability_score`

---

## 2. Tenant Mix Compatibility (30 points)

### Category Saturation Check

```python
# Get category percentage for brand's category
if category == "shop":
    category_percent = mall.tenant_ecosystem.shop_percent
elif category == "f&b":
    category_percent = mall.tenant_ecosystem.food_percent
elif category == "service":
    category_percent = mall.tenant_ecosystem.service_percent

# Score based on saturation level
if category_percent < 30:
    score = 30  # Low saturation - great opportunity
elif category_percent < 45:
    score = 20  # Moderate - balanced mix
elif category_percent < 60:
    score = 10  # High - competitive environment
else:
    score = 5   # Oversaturated - very competitive
```

**Rationale**: Lower saturation means less direct competition and better market opportunity.

### Demographics Fields
- `mall.tenant_ecosystem.shop_percent`
- `mall.tenant_ecosystem.food_percent`
- `mall.tenant_ecosystem.service_percent`
- `brand.operational_profile.category`

---

## 3. Market Position (20 points)

### A. Occupancy Health (15 points)

```python
if occupancy_rate > 85:
    score = 15  # Thriving mall
elif occupancy_rate > 70:
    score = 12  # Stable mall
elif occupancy_rate > 50:
    score = 8   # Moderate performance
elif occupancy_rate >= 0:
    score = 4   # Struggling mall
else:
    score = 0   # Critical condition
```

**Rationale**: Higher occupancy indicates a well-managed, attractive mall with strong foot traffic.

### B. Competition Level (5 points)

```python
if competition_nearby == 0:
    score = 5   # Unique location - monopoly advantage
elif competition_nearby == 1:
    score = 4   # Low competition
elif competition_nearby <= 3:
    score = 2   # Moderate competition
elif competition_nearby <= 5:
    score = 0   # High competition - neutral
else:
    score = -2  # Very high competition - penalty
```

**Competition Nearby**: Number of malls within 3km radius (Haversine distance)

**Rationale**: Less competition means more potential customers and market share.

### Demographics Fields
- `mall.tenant_ecosystem.occupancy_rate`
- `mall.market_position.competition_nearby`

---

## 4. Operational Compatibility (15 points)

### Fixed Baseline

```python
score = 10  # Standard baseline score
```

**Note**: Facility matching was removed as requirements data is not part of demographics. This component now provides a consistent baseline score.

### Demographics Fields
None currently used.

---

## 5. Location & Accessibility (13 points)

### Accessibility Score Mapping

```python
if accessibility_score >= 8:
    score = 13  # Excellent - public transport + ample parking
elif accessibility_score >= 6:
    score = 10  # Good - either transport or parking
elif accessibility_score >= 4:
    score = 7   # Adequate - basic accessibility
elif accessibility_score > 0:
    score = 4   # Limited - minimal access
else:
    score = 2   # Poor - difficult to reach
```

**Accessibility Score Components** (0-9 scale):
- Public transport access: +4 points
- Motorbike parking (>50 spaces): +2 points
- Car parking (>20 spaces): +3 points

### Demographics Fields
- `mall.market_position.accessibility_score`

---

## Final Score Calculation

### 1. Calculate Raw Score

```python
raw_score = (
    financial_score +           # 0-35 pts
    tenant_mix_score +          # 0-30 pts
    market_position_score +     # 0-20 pts
    operational_score +         # 0-15 pts
    location_score              # 0-13 pts
)
# Maximum possible: 113 points
```

### 2. Apply Penalties

```python
# Over-budget penalty
if estimated_rent > max_affordable_rent:
    overage = estimated_rent - max_affordable_rent
    penalty_ratio = overage / max_affordable_rent
    penalty_percent = min(penalty_ratio * 100, 50)  # Cap at 50%
    
    adjusted_score = raw_score * (1 - penalty_percent / 100)
else:
    adjusted_score = raw_score
```

**Example**: 
- Estimated rent: 12M VND
- Max affordable: 10M VND
- Overage: 2M (20% over budget)
- Penalty: 20% reduction in score

### 3. Normalize to 0-100 Scale

```python
final_score = (adjusted_score / 113) * 100
final_score = round(final_score, 2)
```

---

## Score Interpretation

| Score Range | Rating | Recommendation |
|-------------|--------|----------------|
| **85-100** | Highly Compatible | ⭐⭐⭐⭐⭐ Excellent match - highly recommended |
| **70-84** | Compatible | ⭐⭐⭐⭐ Good match - recommended |
| **50-69** | Moderately Compatible | ⭐⭐⭐ Acceptable with considerations |
| **30-49** | Low Compatibility | ⭐⭐ Risky - not recommended |
| **0-29** | Not Compatible | ⭐ Poor match - avoid |

---

## Complete Example

### Input Data

**Mall Demographics**:
```python
{
  "tenant_ecosystem": {
    "shop_percent": 35,
    "food_percent": 25,
    "service_percent": 40,
    "occupancy_rate": 78.5
  },
  "pricing_context": {
    "avg_rent_per_sqm": 150000
  },
  "market_position": {
    "competition_nearby": 2,
    "accessibility_score": 6.5
  }
}
```

**Brand Demographics**:
```python
{
  "financial_performance": {
    "income_stability_score": 7.5
  },
  "financial_capacity": {
    "max_affordable_rent": 10000000,
    "comfortable_rent_range": [6000000, 10000000]
  },
  "operational_profile": {
    "category": "f&b",
    "space_requirement_m2": 50
  }
}
```

### Step-by-Step Calculation

**1. Financial (35 pts)**:
```
Estimated rent = 150,000 × 50 = 7,500,000 VND

Comfortable range: [6M, 10M], rent: 7.5M ✓
  → 20 points

Max affordable: 10M, rent: 7.5M ✓
  → 10 points

Income stability: 7.5 ≥ 6.0 ✓
  → 3 points

Financial total = 33 points
```

**2. Tenant Mix (30 pts)**:
```
Category: f&b
Food percent: 25% < 30 (low saturation) ✓
  → 30 points
```

**3. Market Position (20 pts)**:
```
Occupancy: 78.5% > 70 ✓
  → 12 points

Competition: 2 malls ≤ 3 ✓
  → 2 points

Market Position total = 14 points
```

**4. Operational (15 pts)**:
```
Baseline → 10 points
```

**5. Location (13 pts)**:
```
Accessibility: 6.5 ≥ 6 ✓
  → 10 points
```

### Final Calculation

```
Raw score = 33 + 30 + 14 + 10 + 10 = 97 points

Penalty check:
  Estimated rent (7.5M) ≤ Max affordable (10M) ✓
  → No penalty

Adjusted score = 97 points

Final score = (97 / 113) × 100 = 85.84

Rating: "Highly Compatible" ⭐⭐⭐⭐⭐
```

---

## Fields Summary

### Mall Demographics (6 fields)
1. `tenant_ecosystem.shop_percent`
2. `tenant_ecosystem.food_percent`
3. `tenant_ecosystem.service_percent`
4. `tenant_ecosystem.occupancy_rate`
5. `pricing_context.avg_rent_per_sqm`
6. `market_position.competition_nearby`
7. `market_position.accessibility_score`

### Brand Demographics (5 fields)
1. `financial_performance.income_stability_score`
2. `financial_capacity.max_affordable_rent`
3. `financial_capacity.comfortable_rent_range`
4. `operational_profile.category`
5. `operational_profile.space_requirement_m2`

**Total**: 10 demographics fields used in scoring

---

## Notes

- All demographic fields are automatically calculated by the backend
- Scores are recalculated whenever mall/brand demographics are updated
- The 113-point scale allows for granular differentiation between recommendations
- Penalty system prevents recommending unaffordable locations even if other factors are good
