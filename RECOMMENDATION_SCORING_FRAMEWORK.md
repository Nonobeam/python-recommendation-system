# Recommendation Scoring Framework

## Overview

This system evaluates brand-mall compatibility using a rule-based scoring framework (0-100 scale). The scoring is fully explainable and based on mall and brand demographics data.

## Scoring Dimensions

The system evaluates **5 core dimensions** with weighted components:

### 1. Financial Compatibility (35 points max)

Evaluates whether the brand can afford the mall's pricing structure.

**Rent Affordability Analysis:**
- Compare estimated booth rent against brand's `maxAffordableRent` and `comfortableRentRange`
- Calculate estimated rent: `booth_size_m2 × mall's avgRentPerSqm`
- Scoring:
  - Rent ≤ comfortable lower bound: **30 points**
  - Rent ≤ comfortable upper bound: **25 points**
  - Rent ≤ max affordable: **15 points**
  - Rent > max affordable: **5 points** (over budget)
  
**Income Stability Factor:**
- `incomeStabilityScore ≥ 8`: **+5 points**
- `incomeStabilityScore ≥ 6`: **+3 points**
- Lower scores: no bonus

**Data Requirements:**
- Brand: `space_requirement_m2`, `max_affordable_rent`, `comfortable_rent_range`, `income_stability_score`
- Mall: `avg_rent_per_sqm`

---

### 2. Tenant Mix & Category Fit (30 points max)

Evaluates category representation to avoid oversaturation.

**Category Matching:**
- Brand category is mapped to mall category percentages:
  - **Food/Entertainment/Giải trí** → `food_percent`
  - **Retail/Clothing/Shop** → `shop_percent`
  - **Service/Dịch vụ** → `service_percent`

**Scoring:**
- Category < 25%: **25 points** (under-represented, excellent opportunity)
- Category < 40%: **20 points** (balanced)
- Category < 55%: **12 points** (getting crowded)
- Category < 70%: **5 points** (somewhat oversaturated)
- Category ≥ 70%: **0 points** (oversaturated)

**Baseline Scoring:**
- Category identified but percentages missing: **15 points**
- No category specified: **10 points**

**Data Requirements:**
- Brand: `operational_profile.category`
- Mall: `tenant_ecosystem.food_percent`, `shop_percent`, `service_percent`

**Example:**
```json
{
  "brand_category": "Giải trí",
  "mall_service_percent": 30,
  "score": 20,
  "explanation": "Category is balanced (30% < 40%)"
}
```

---

### 3. Market Position & Demographics (20 points max)

Evaluates alignment between brand positioning and mall characteristics.

**Mall Type Compatibility:**
- Mall type matches brand's preferred types: **+10 points**
- Mall type provided but not preferred: **+5 points**
- Mall type missing: **+3 points** (minimal baseline)

**Occupancy Health Indicator:**
- Occupancy > 85%: **+5 points** (healthy mall)
- Occupancy > 70%: **+3 points** (stable)
- Occupancy > 50%: **+1 point** (moderate)
- Occupancy ≤ 50%: **0 points** (struggling)
- Occupancy < 0: **-2 points** (penalty for negative indicators)

**Data Requirements:**
- Brand: `requirements.preferred_mall_types`
- Mall: `market_position.mall_type`, `tenant_ecosystem.occupancy_rate`

**Note:** Spending power distribution matching has been **removed** from this version.

---

### 4. Operational Compatibility (15 points max)

Evaluates facility requirements alignment.

**Facilities Match:**
- Score = `(matched_facilities / required_facilities) × 10`
- Common facilities: electricity, water, ventilation, drainage, gas, internet
- No facilities requirements: **+5 points** (baseline)

**Data Requirements:**
- Brand: `requirements.required_facilities`
- Mall: `facilities[]`

**Example:**
```json
{
  "required_facilities": ["electricity", "water", "ventilation"],
  "available_facilities": ["electricity", "water", "internet"],
  "matched": 2,
  "score": 6.67,
  "explanation": "Matched 2/3 required facilities"
}
```

**Note:** Peak hours overlap checking has been **removed** from this version.

---

### 5. Location & Accessibility (13 points max)

Evaluates mall location proximity and accessibility.

**Distance Scoring:**
- Distance ≤ 5km: **10 points** (excellent proximity)
- Distance ≤ 10km: **7 points** (good distance)
- Distance ≤ 20km: **4 points** (fair distance)
- Distance > 20km: **1 point** (poor location)
- Unknown distance: **5 points** (neutral baseline)

**Accessibility Bonus:**
- Accessibility score ≥ 8: **+3 points**
- Accessibility score ≥ 6: **+2 points**
- Accessibility score > 0: **+1 point**

**Data Requirements:**
- Mall: `market_position.location_distance`, `market_position.accessibility_score`

**Example:**
```json
{
  "location_distance": "7km",
  "accessibility_score": 9,
  "score": 10,
  "explanation": "Mall within 10km (7 pts) + High accessibility (3 pts)"
}
```

---

## Final Score Calculation

### Step 1: Component Score Summation
1. Sum all valid component scores
2. Calculate maximum possible score based on available components
3. Normalize to 0-100 scale: `(total / max_possible_score) × 100`

### Step 2: Adjustment Factors

Apply these multipliers to the normalized score:

**Penalties:**
- **Over Budget:** If `estimated_rent > max_affordable_rent`: `score × 0.7` (30% penalty)
- **Low Occupancy:** If `occupancy_rate < 40%`: `score × 0.8` (20% penalty)
- **Oversaturation:** If any category > 70%: `score × 0.85` (15% penalty)

**Note:** Tenant success metrics (turnover/renewal bonuses) have been **removed** from this version.

### Step 3: Final Score
Clamp the result between 0 and 100.

---

## Example Scoring Calculation

### Input Data

**Brand:**
```json
{
  "financial_capacity": {
    "max_affordable_rent": 10000000,
    "comfortable_rent_range": [5000000, 8000000]
  },
  "financial_performance": {
    "income_stability_score": 8.5
  },
  "operational_profile": {
    "category": "Giải trí",
    "space_requirement_m2": 50
  },
  "requirements": {
    "preferred_mall_types": ["SHOPPING_MALL"],
    "required_facilities": ["electricity", "water", "ventilation"]
  }
}
```

**Mall:**
```json
{
  "pricing_context": {
    "avg_rent_per_sqm": 150000
  },
  "tenant_ecosystem": {
    "service_percent": 30,
    "occupancy_rate": 85.5
  },
  "market_position": {
    "mall_type": "SHOPPING_MALL",
    "accessibility_score": 9,
    "location_distance": "5km"
  },
  "facilities": ["electricity", "water", "internet", "parking"]
}
```

### Calculation

**1. Financial (35 max):**
- Estimated rent = 50 × 150,000 = 7,500,000 VND
- Within comfortable range (5M-8M): **25 points**
- Income stability ≥ 8: **+5 points**
- **Total: 30 points**

**2. Tenant Mix (30 max):**
- Category: Giải trí → service_percent = 30%
- 30% is balanced (25% < 30% < 40%): **20 points**
- **Total: 20 points**

**3. Market Position (20 max):**
- Mall type matches preferred: **10 points**
- Occupancy 85.5% > 85%: **+5 points**
- **Total: 15 points**

**4. Operational (15 max):**
- Required: 3 facilities, Matched: 2 (electricity, water)
- Score = (2/3) × 10 = **6.67 points**
- **Total: 7 points**

**5. Location (13 max):**
- Distance ≤ 5km: **10 points**
- Accessibility ≥ 8: **+3 points**
- **Total: 13 points**

**Base Score:**
- Sum = 30 + 20 + 15 + 7 + 13 = **85 points**
- Max possible = 35 + 30 + 20 + 15 + 13 = **113 points**
- Normalized = (85/113) × 100 = **75.22%**

**Adjustments:**
- No over-budget penalty (7.5M < 10M max)
- No low occupancy penalty (85.5% > 40%)
- No oversaturation penalty (30% < 70%)

**Final Score: 75.22 / 100** ✅

---

## Removed Features

The following features were removed in this version to simplify the scoring model:

### From Mall Demographics:
- ❌ `visitor_profile` (peak_hours, spending_power_distribution)
- ❌ `zone_performance` (zone-level statistics)
- ❌ `tenant_success_metrics` (renewal_rate, tenant_turnover_rate)

### From Scoring Logic:
- ❌ Peak hours overlap checking
- ❌ Spending power distribution matching
- ❌ Zone matching bonus
- ❌ Tenant turnover rate bonus (< 10%)
- ❌ Tenant renewal rate bonus (> 70%)

### Simplified Data:
- `avg_rent_per_sqm` now returns `0` instead of `null` when no data available

---

## API Response Format

```json
{
  "success": true,
  "result": {
    "brand_id": "brand_123",
    "mall_id": "mall_456",
    "final_score": 75.22,
    "component_scores": {
      "financial": 30,
      "tenant_mix": 20,
      "market_position": 15,
      "operational": 7,
      "location": 13
    },
    "explanations": {
      "financial": [
        "Estimated rent: 7500000",
        "Rent is within upper comfortable range.",
        "High income stability. Bonus points added."
      ],
      "tenant_mix": [
        "Category = food/entertainment. Mall service_percent = 30%.",
        "Category is balanced."
      ],
      "market_position": [
        "Mall type matches preferred types.",
        "Mall is healthy (>85% occupancy)."
      ],
      "operational": [
        "Matched 2 / 3 required facilities."
      ],
      "location": [
        "Mall is within 5km: excellent proximity.",
        "High accessibility score. +3 points."
      ]
    },
    "calculation_timestamp": "2025-12-04T10:00:00Z"
  }
}
```

---

## Data Requirements Summary

### Minimum Required Data for Scoring:

**Brand:**
- `financial_capacity.max_affordable_rent` (Financial)
- `operational_profile.category` (Tenant Mix)

**Mall:**
- `pricing_context.avg_rent_per_sqm` (Financial)
- `tenant_ecosystem.food_percent/shop_percent/service_percent` (Tenant Mix)
- `tenant_ecosystem.occupancy_rate` (Market Position)

### Recommended Data for Best Results:

**Brand:**
- `financial_capacity.comfortable_rent_range`
- `financial_performance.income_stability_score`
- `operational_profile.space_requirement_m2`
- `requirements.preferred_mall_types`
- `requirements.required_facilities`

**Mall:**
- `market_position.mall_type`
- `market_position.accessibility_score`
- `market_position.location_distance`
- `facilities[]`

