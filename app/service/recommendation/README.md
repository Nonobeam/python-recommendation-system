# Demographics-Based Recommendation System (Business Rules Version)

## Overview

This recommendation system calculates compatibility scores between brands and malls using a business-rule based scoring system (no ML vector similarity). All scoring is fully explainable and based on the latest mall/brand demographics contract.

## Architecture (Updated)

### Data Layer
- Uses `repositories.py` for retrieving the latest demographics (brand/mall) from cache/database.

### Scoring Logic
- `business_match_scorer.py`: Implements all business rules for matching brands and malls, following explicit scoring criteria:
    - **Financial Compatibility** (35 pts max)
    - **Tenant Mix/Category Fit** (30 pts max)
    - **Market Position & Demographics** (20 pts max)
    - **Operational Compatibility** (15 pts max)
    - **Location & Accessibility** (13 pts max)
- Each section is scored via clear rule-based checks (banded thresholds, bonuses, penalties), not by feature vector math.
- Legacy vector logic and calculators have been **removed**.

### Service Layer
- SingleMatchService / BatchMatchService instantiate a `BusinessMatchScorer` for each brand/mall match and return the new output contract.

## API

### POST `/pri/api/v1/recommendations/score`
Input:
```
{
  "brand_id": "...",
  "mall_id": "..."
}
```
Response:
```
{
  "success": true,
  "result": {
    "brand_id": "...",
    "mall_id": "...",
    "final_score": 85.0,
    "component_scores": {
      "financial": 32,
      "tenant_mix": 23,
      "market_position": 17,
      "operational": 13,
      "location": 10
    },
    "explanations": {
      "financial": ["Estimated rent ... within budget",...],
      "tenant_mix": ["Category is under-represented",...],
      ...
    },
    "calculation_timestamp": "2025-10-30T10:00:00"
  }
}
```

### POST `/pri/api/v1/recommendations/batch-score`
Input:
```
{
  "brand_id": "...",
  "mall_ids": ["...", ...]
}
```
Response:
```
{
  "success": true,
  "brand_id": "...",
  "results": [
    {
      "mall_id": "...",
      "final_score": 73.7,
      "component_scores": {...},
      "explanations": {...},
      "calculation_timestamp": "2025-10-30T10:00:00"
    }, ...
  ]
}
```

### Error Handling

If brand/mall data is missing, component scores and explanations are null and final_score is NaN.

---

## Testing
- Test each business rule directly (unit tests on BusinessMatchScorer's component methods)
- Test score explanations for clarity

## Migration Notes
- All previous vector logic and legacy score calculators are obsolete and can be deleted.
- Only new business-aligned fields are used; legacy field support should be purged from data and mocks/tests as feasible.
