# Scoring System Documentation

## Overview

The recommendation system uses a rule-based scoring approach to evaluate compatibility between brands, malls, and booths. The scoring is fully explainable and based on business rules rather than machine learning models. The system consists of two main scoring components:

1. **BusinessMatchScorer**: Evaluates compatibility between a brand and a mall
2. **BoothScorer**: Evaluates compatibility between a brand and a specific booth within a mall

## Architecture

### Scoring Flow

```
Brand Request
    ↓
BusinessMatchScorer (Brand ↔ Mall)
    ↓
Mall Score (0-100)
    ↓
BoothScorer (Brand ↔ Booth + Mall Score)
    ↓
Booth Score (0-100) + Composite Score
```

### Score Types

- **Mall Score**: Compatibility score between brand and mall (0-100)
- **Booth Score**: Compatibility score between brand and specific booth (0-100)
- **Composite Score**: Weighted combination of mall score (40%) and booth score (60%)

## BusinessMatchScorer: Brand-Mall Compatibility

The `BusinessMatchScorer` evaluates how well a brand matches with a mall across five dimensions.

### Component Scores

#### 1. Financial Compatibility (35 points max)

Evaluates whether the brand can afford the mall's pricing based on estimated rent.

**Calculation:**
- Estimates rent: `space_required_m2 × avg_rent_per_sqm`
- Compares against brand's financial capacity:
  - **Comfortable Range Available:**
    - Rent ≤ lower bound: **30 points** (well within comfortable budget)
    - Rent ≤ upper bound: **25 points** (within upper comfortable range)
    - Rent ≤ max_affordable_rent: **15 points** (affordable but tight)
    - Rent > max_affordable_rent: **5 points** (over budget)
  - **Only Max Affordable Available:**
    - Rent ≤ max_affordable_rent: **20 points** (within affordable range)
    - Rent > max_affordable_rent: **5 points** (over budget)

**Income Stability Bonus:**
- Income stability score ≥ 8: **+5 points**
- Income stability score ≥ 6: **+3 points**
- Income stability score < 6: **0 points**

**Maximum:** 35 points

#### 2. Tenant Mix (30 points max)

Evaluates category representation in the mall to avoid oversaturation.

**Category Matching:**
- Identifies brand category (restaurant/cafe, retail/clothing, service, or other)
- Retrieves corresponding mall percentage:
  - Food: `food_percent`
  - Retail: `shop_percent`
  - Service: `service_percent`

**Scoring:**
- Category percent < 25%: **25 points** (under-represented, excellent mix)
- Category percent < 40%: **20 points** (balanced)
- Category percent < 55%: **12 points** (getting crowded)
- Category percent < 70%: **5 points** (somewhat oversaturated)
- Category percent ≥ 70%: **0 points** (oversaturated)

**Zone Match Bonus:**
- Brand's target zones match available mall zones: **+5 points**

**Maximum:** 30 points

#### 3. Market Position (20 points max)

Evaluates alignment between brand positioning and mall demographics.

**Spending Power Alignment:**
- Premium/Luxury brand: `premium_percent × 0.4` points
- Mid-range brand: `mid_range_percent × 0.4` points
- Budget brand: `budget_percent × 0.4` points

**Mall Type Match:**
- Mall type matches brand's preferred types: **+10 points**
- Mall type not preferred: **+5 points** (neutral)

**Occupancy Rate Bonus:**
- Occupancy > 85%: **+5 points** (healthy)
- Occupancy > 70%: **+3 points** (stable)
- Occupancy > 50%: **+1 point** (moderate)
- Occupancy ≤ 50%: **-2 points** (struggling, penalty)

**Maximum:** 20 points

#### 4. Operational Compatibility (15 points max)

Evaluates facilities and operating hours alignment.

**Facilities Match:**
- Score = `(matched_facilities / required_facilities) × 10`
- Examples: electricity, water, ventilation, drainage, gas, internet

**Operating Hours Overlap:**
- Brand hours overlap mall peak hours: **+5 points**
- No overlap or missing data: **+2 points** (partial)

**Maximum:** 15 points

#### 5. Location & Accessibility (13 points max)

Evaluates mall location proximity and accessibility.

**Distance Scoring:**
- Distance ≤ 5km: **10 points** (excellent proximity)
- Distance ≤ 10km: **7 points** (good distance)
- Distance ≤ 20km: **4 points** (fair distance)
- Distance > 20km: **1 point** (poor location)

**Accessibility Bonus:**
- Accessibility score ≥ 8: **+3 points**
- Accessibility score ≥ 6: **+2 points**
- Accessibility score < 6: **0 points**

**Maximum:** 13 points

### Final Score Calculation

1. **Component Score Summation:**
   - Sum all valid component scores
   - Calculate maximum possible score based on available components
   - Normalize: `(total / max_possible_score) × 100`

2. **Adjustment Factors:**
   - **Over Budget Penalty:** If estimated rent > max_affordable_rent: `final_score × 0.7`
   - **Low Occupancy Penalty:** If occupancy < 40%: `final_score × 0.8`
   - **Oversaturation Penalty:** If any category > 70%: `final_score × 0.85`
   - **Low Turnover Bonus:** If turnover < 10%: `final_score × 1.1`
   - **High Renewal Bonus:** If renewal rate > 70%: `final_score × 1.05`

3. **Final Score:** Clamped between 0 and 100

## BoothScorer: Brand-Booth Compatibility

The `BoothScorer` evaluates how well a specific booth matches a brand's requirements, incorporating the mall score as inheritance.

### Component Scores

#### 1. Financial Compatibility (35 points max)

Evaluates whether the booth rent price fits the brand's budget.

**Calculation:**
- Uses actual booth `rent_price` if available
- If missing, estimates: `booth_size_m2 × 1,000,000` (fallback)
- Compares against brand's financial capacity (same logic as BusinessMatchScorer)

**Maximum:** 35 points

#### 2. Location (25 points max)

Evaluates booth location preferences.

**Floor Level Match:**
- Booth floor matches preferred floors: **+10 points**
- Booth floor not preferred: **+5 points**
- No preference or unknown: **+5 points**

**Facilities Match:**
- Score = `(matched_facilities / required_facilities) × 10`
- Booth facilities: electricity, water, ventilation, drainage, gas, internet

**Zone Match:**
- Booth zone matches target zones: **+5 points**
- No match or missing: **0 points**

**Maximum:** 25 points

#### 3. Physical Compatibility (25 points max)

Evaluates physical booth characteristics.

**Size Match:**
- Size difference ≤ 10%: **15 points** (closely matches)
- Size difference ≤ 20%: **10 points** (within 20%)
- Size difference ≤ 30%: **5 points** (within 30%)
- Size difference > 30%: **0 points** (significant difference)

**Frontage Width:**
- Frontage ≥ preferred: **+5 points**
- Frontage < preferred: **+2 points**

**Ceiling Height:**
- Ceiling ≥ preferred: **+3 points**
- Ceiling < preferred: **+1 point**

**Shape Match:**
- Shape matches preference: **+2 points**
- Shape doesn't match: **0 points**

**Maximum:** 25 points

#### 4. Mall Inheritance (15 points max)

Inherits score from the mall compatibility evaluation.

**Calculation:**
- `mall_score_normalized = (mall_score / 100) × 15`
- Inherits up to 15 points based on mall compatibility

**Maximum:** 15 points

### Final Score Calculation

1. **Booth Score:**
   - Sum all valid component scores
   - Normalize: `(total / max_possible_score) × 100`
   - Maximum possible: 100 points (35 + 25 + 25 + 15)

2. **Composite Score:**
   - Weighted combination: `(mall_score × 0.4) + (booth_score × 0.6)`
   - This gives more weight to booth-specific factors while considering mall compatibility

## Scoring Utilities

### Helper Functions

**`is_valid_number(value)`**
- Checks if a value is a valid number (not None, not NaN)
- Used to validate numeric inputs before calculations

**`safe_get_number(data, key, default=None)`**
- Safely extracts a number from a dictionary
- Returns None if value is invalid or missing
- Prevents calculation errors from invalid data

## Score Output Format

### BusinessMatchScorer Output

```python
{
    "final_score": 85.0,  # 0-100
    "component_scores": {
        "financial": 32,      # 0-35
        "tenant_mix": 23,      # 0-30
        "market_position": 17, # 0-20
        "operational": 13,     # 0-15
        "location": 10         # 0-13
    },
    "explanations": {
        "financial": [
            "Estimated rent: 5000000",
            "Rent is well within comfortable budget range.",
            "High income stability. Bonus points added."
        ],
        # ... other components
    }
}
```

### BoothScorer Output

```python
{
    "booth_score": 78.5,      # 0-100 (normalized booth score)
    "mall_score": 85.0,       # 0-100 (inherited from mall match)
    "composite_score": 81.1,   # 0-100 (weighted: 40% mall + 60% booth)
    "component_scores": {
        "financial": 30,          # 0-35
        "location": 20,           # 0-25
        "physical": 18,           # 0-25
        "mall_inheritance": 13    # 0-15
    },
    "explanations": {
        "financial": [
            "Booth rent price: 4500000",
            "Rent is well within comfortable budget range.",
            "High income stability. Bonus points added."
        ],
        # ... other components
    }
}
```

## Handling Missing Data

### Invalid Scores

- If a component cannot be calculated (missing required data), it returns `None`
- Components returning `None` are excluded from the final score calculation
- If all components are invalid, the final score is `NaN`

### Partial Scoring

- The system can calculate scores even with partial data
- Missing components reduce the maximum possible score
- Final score is normalized based on available components only

## Usage Examples

### Calculating Mall Score

```python
from app.service.recommendation.business_match_scorer import BusinessMatchScorer

brand_data = {...}  # Brand demographics
mall_data = {...}   # Mall demographics

scorer = BusinessMatchScorer(brand_data, mall_data)
result = scorer.compute_final_score()

print(f"Mall Score: {result['final_score']}")
print(f"Component Scores: {result['component_scores']}")
```

### Calculating Booth Score

```python
from app.service.recommendation.booth_scorer import BoothScorer

brand_data = {...}  # Brand demographics
booth_data = {...}  # Booth details
mall_score = 85.0   # From BusinessMatchScorer

scorer = BoothScorer(brand_data, booth_data, mall_score)
result = scorer.compute_final_score()

print(f"Booth Score: {result['booth_score']}")
print(f"Composite Score: {result['composite_score']}")
```

## Performance Considerations

- Scoring is synchronous and CPU-bound
- For batch operations, scores are calculated sequentially
- Each score calculation is independent and can be parallelized if needed
- Scores are deterministic: same inputs produce same outputs

## Future Enhancements

Potential improvements to consider:
- Caching of intermediate calculations
- Parallel batch scoring
- Configurable weight adjustments
- Machine learning integration for weight optimization
- Real-time score updates when data changes

