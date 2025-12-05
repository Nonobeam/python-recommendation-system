# Troubleshooting Empty Recommendation Results

This document explains why recommendation endpoints may return empty results and how to fix them.

## Problem: Empty Mall/Brand Recommendations

### Symptoms

```json
{
  "success": true,
  "data": {
    "brand_id": "...",
    "total_results": 0,
    "page": 1,
    "page_size": 10,
    "total_pages": 0,
    "has_more": false,
    "results": []
  }
}
```

### Common Causes

## 1. Incomplete Brand Demographics

**Issue:** Brand demographics are missing required fields needed for scoring.

**Check the logs for:**
```
WARNING - No compatible malls found for brand_id=...
```

**Required Fields:**

### Financial Capacity
```json
{
  "financialCapacity": {
    "maxAffordableRent": 1602476,
    "comfortableRentRange": [1068317, 1602476],
    "currentRentToIncomeRatio": null
  }
}
```

### Operational Profile
```json
{
  "operationalProfile": {
    "category": "Giải trí",
    "operatingHours": "10:00-22:00",
    "space_requirement_m2": 50  // ⚠️ RECOMMENDED but not required
  }
}
```

### Financial Performance
```json
{
  "financialPerformance": {
    "avgDailyNetIncome": 178053,
    "avgMonthlyNetIncome": 5341587,
    "incomeStabilityScore": 8.5  // ⚠️ RECOMMENDED for better scoring
  }
}
```

**Note:** As of the latest update, the system can now score even when `space_requirement_m2` is missing. It will use alternative financial indicators like `maxAffordableRent` and mall's `avg_rent_per_sqm` for approximate scoring.

## 2. Incomplete Mall Demographics

**Issue:** Mall demographics have insufficient data for scoring.

**Problematic Mall Data Examples:**

```json
{
  "tenantEcosystem": {
    "totalBooths": 0,  // ❌ No booths = no recommendations
    "occupancyRate": 0.00,
    "occupiedBooths": 0
  },
  "pricingContext": {
    "avgRentPerSqm": 0  // ⚠️ Makes financial scoring difficult
  }
}
```

**Good Mall Data:**
```json
{
  "tenantEcosystem": {
    "totalBooths": 5,
    "occupancyRate": 40.00,
    "occupiedBooths": 2,
    "foodPercent": 20,
    "shopPercent": 50,
    "servicePercent": 30
  },
  "pricingContext": {
    "avgRentPerSqm": 201,
    "managementFeeUsd": 123.00,
    "priceTrend6m": "stable"
  }
}
```

## 3. NaN Scores (All Malls Filtered Out)

**Issue:** Scoring algorithm returns NaN when no valid scoring components can be calculated.

**Scoring Components:**
1. **Financial** (35 pts) - Requires rent comparison data
2. **Tenant Mix** (30 pts) - Requires category percentages
3. **Market Position** (20 pts) - Requires spending power distribution
4. **Operational** (15 pts) - Requires facilities or operating hours
5. **Location** (13 pts) - Requires accessibility score or distance

**Minimum Requirement:** At least ONE component must return a valid score. If ALL components return `None`, the final score will be NaN and the mall/brand will be filtered out.

**Improved Resilience (Latest Update):**
The financial scoring component has been improved to handle missing data better:
- If `space_requirement_m2` is missing, it uses alternative financial indicators
- If `avg_rent_per_sqm` is available with `maxAffordableRent`, it estimates affordability
- Income stability scoring is independent and always applied when available

## 4. No Active Malls/Brands in Database

**Check the logs for:**
```
WARNING - No active malls found in database
WARNING - No active brands found in database
```

**Solution:**
Ensure there are active malls/brands in the database:
```sql
SELECT COUNT(*) FROM platform_service.mall WHERE status = 'ACTIVE';
SELECT COUNT(*) FROM platform_service.brand WHERE status = 'ACTIVE';
```

## 5. Missing Demographics Records

**Check the logs for:**
```
ERROR - NOT_FOUND [entity:xxxxx] No data found in database
```

**Solution:**
Ensure demographics are calculated and stored:
```sql
SELECT COUNT(*) FROM platform_service.brand_demographics;
SELECT COUNT(*) FROM platform_service.mall_demographics;
```

If missing, run the demographics calculation process or ETL job.

## Diagnostic Steps

### Step 1: Check Brand Demographics

```bash
# Query the API or check logs
curl "http://localhost:8000/pri/api/v1/recommendations/malls?brandId={brand_id}"
```

Look for log messages showing what data is being retrieved.

### Step 2: Verify Required Fields

Ensure the brand has:
- ✅ `financialCapacity.maxAffordableRent` OR `comfortableRentRange`
- ✅ `operationalProfile.category`
- ⚠️ `operationalProfile.space_requirement_m2` (recommended but optional)
- ⚠️ `financialPerformance.incomeStabilityScore` (optional, improves scoring)

### Step 3: Check Mall Data Quality

Count malls with valid data:
```sql
SELECT 
  COUNT(*) as total_malls,
  COUNT(CASE WHEN (meta_data->>'tenantEcosystem')::jsonb->>'totalBooths' != '0' THEN 1 END) as malls_with_booths,
  COUNT(CASE WHEN (meta_data->>'pricingContext')::jsonb->>'avgRentPerSqm' IS NOT NULL THEN 1 END) as malls_with_pricing
FROM platform_service.mall_demographics;
```

### Step 4: Review Scoring Logic

Check what components are scoring:
1. Enable debug logging in Python app
2. Look for component score breakdowns in responses
3. Identify which components return `null`

## Solutions

### Solution 1: Populate Missing Brand Data

Ensure the demographics calculation includes all required fields:
```java
// In your demographics calculator
BrandDemographics demographics = BrandDemographics.builder()
  .financialCapacity(calculateFinancialCapacity(brand))
  .operationalProfile(calculateOperationalProfile(brand))  // Include space_requirement_m2
  .financialPerformance(calculateFinancialPerformance(brand))  // Include incomeStabilityScore
  .build();
```

### Solution 2: Improve Mall Data Quality

Ensure malls have:
- At least 1 booth (`totalBooths > 0`)
- Pricing information (`avgRentPerSqm`)
- Category distribution (`foodPercent`, `shopPercent`, etc.)
- Accessibility score or location distance

### Solution 3: Use Fallback Scoring (Implemented)

The latest update improves scoring resilience:
- Financial scoring now works with partial data
- Income stability can boost scores independently
- Rough pricing estimates used when exact calculations aren't possible

### Solution 4: Lower Scoring Thresholds

If the scoring is too strict for your use case, you can:
1. Adjust component weights in `score_calculator.py`
2. Modify threshold values in `business_match_scorer.py`
3. Allow lower minimum scores (currently filters out NaN only)

## Prevention

### 1. Data Validation

Add validation before saving demographics:
```java
@PrePersist
public void validateDemographics() {
  if (financialCapacity == null || financialCapacity.getMaxAffordableRent() == null) {
    throw new ValidationException("Missing required financial capacity data");
  }
  // Add more validations
}
```

### 2. Default Values

Provide sensible defaults for optional fields:
```java
if (brand.getOperationalProfile().getSpaceRequirementM2() == null) {
  // Estimate based on category
  brand.getOperationalProfile().setSpaceRequirementM2(estimateSpaceRequirement(category));
}
```

### 3. Regular Data Audits

Schedule periodic checks for data quality:
```sql
-- Find brands with incomplete demographics
SELECT b.brand_id, b.name
FROM platform_service.brand b
LEFT JOIN platform_service.brand_demographics bd ON b.brand_id = bd.brand_id
WHERE bd.brand_id IS NULL
   OR (bd.meta_data->>'financialCapacity')::jsonb->>'maxAffordableRent' IS NULL;
```

### 4. Monitoring

Set up alerts for:
- High rate of empty results (> 50%)
- Missing demographics records
- NaN scores in recommendation responses

## Testing

### Test with Known Good Data

```bash
# Use a brand with complete demographics
curl "http://localhost:8000/pri/api/v1/recommendations/malls?brandId=known-good-brand-id"
```

### Test Partial Data Scenarios

```bash
# Test brand missing space_requirement_m2
# Should now return results with adjusted financial scoring
```

### Test Edge Cases

- Brand with negative transaction (startup logic)
- Mall with zero booths (should be filtered)
- Brand with only operational data (should partially score)

## Related Documentation

- `STARTUP_BRAND_LOGIC.md` - How negative transactions are handled
- `SCORING_DOCUMENTATION.md` - Detailed scoring algorithm
- `app/service/recommendation/README.md` - Recommendation system overview

## Support Checklist

When investigating empty results:

- [ ] Check application logs for warnings/errors
- [ ] Verify brand demographics exist in database
- [ ] Verify mall demographics exist in database
- [ ] Check if brand has required financial fields
- [ ] Check if malls have booths and pricing data
- [ ] Review scoring component explanations (if available)
- [ ] Test with known good brand/mall combination
- [ ] Check Redis cache for stale data
- [ ] Verify database query performance
- [ ] Review recent code changes to scoring logic

