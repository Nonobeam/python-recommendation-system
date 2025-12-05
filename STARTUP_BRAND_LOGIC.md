# Startup Brand Detection and Cheap Booth Recommendation

## Overview

This document describes the logic for detecting startup brands with negative transaction values and recommending affordable booths to them.

## Problem Statement

When calculating brand transactions, some brands may have negative transaction values. This typically indicates:
- The brand is a startup with minimal or no revenue history
- The brand has lower financial capacity
- The brand may have initial costs exceeding income

For these brands, we need to recommend booths with affordable pricing to match their financial constraints.

## Solution

### Detection Logic

The system detects startup brands by examining the `transaction` field in the brand's financial capacity data:

```python
transaction_value = fc.get("transaction", 0)

if transaction_value is not None and transaction_value < 0:
    filters["max_price"] = STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD
```

### Cheap Booth Price Threshold

When a brand is identified as a startup (negative transaction value), the system applies a price ceiling to booth recommendations:

- **Constant Name**: `STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD`
- **Default Value**: 2,000,000 (2 million)
- **Environment Variable**: `STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD`
- **Configuration**: Can be customized via `.env` file

### Affected Endpoints

This logic is applied to both recommendation endpoints:

1. **GET /pri/api/v1/recommendations/malls**
   - Recommends malls for a brand
   - Uses booth filter extractor which applies startup logic
   - Filters malls based on availability of cheap booths for startup brands

2. **GET /pri/api/v1/recommendations/brands**
   - Recommends brands for a mall
   - Uses booth filter extractor which applies startup logic
   - Filters brands based on their financial capacity and booth requirements

## Implementation Details

### File Changes

1. **app/constants.py**
   - Added `STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD` constant
   - Loads value from environment variable with default of 2,000,000

2. **app/service/recommendation/booth_filter_extractor.py**
   - Modified `extract_filters_from_brand()` method
   - Added transaction value detection logic
   - Applies cheap booth price threshold for startup brands

### Code Flow

```
1. Brand requests recommendations
   |
2. System extracts brand demographics
   |
3. System checks financial_capacity.transaction value
   |
4. If transaction < 0:
   |   Set max_price = STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD
   |   Log warning about startup detection
   |
5. Else if max_affordable_rent > 0:
   |   Set max_price = max_affordable_rent
   |
6. Filter booths/malls based on max_price
   |
7. Return recommendations
```

### Logging

When a startup brand is detected, the system logs a warning message:

```
Brand {brand_id} has negative transaction value ({transaction_value}), 
applying cheap booth price threshold: {STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD}
```

This helps track and monitor startup brand recommendations in the system.

## Configuration

### Environment Variable Setup

Add to your `.env` file:

```env
STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD=2000000
```

To change the threshold, modify the value in your `.env` file. The system will load the new value on restart.

### Recommended Threshold Values

Based on market analysis:
- **Budget Startups**: 1,000,000 - 1,500,000
- **Standard Startups**: 2,000,000 - 3,000,000 (default)
- **Growth-Stage Startups**: 3,000,000 - 5,000,000

## Example Scenarios

### Scenario 1: Startup Brand with Negative Transactions

**Input:**
```json
{
  "brand_id": "startup-123",
  "financial_capacity": {
    "transaction": -500000,
    "max_affordable_rent": 5000000
  }
}
```

**Result:**
- System detects negative transaction value
- Applies `max_price = 2,000,000` (ignoring max_affordable_rent)
- Recommends only booths with rent_price <= 2,000,000

### Scenario 2: Established Brand with Positive Transactions

**Input:**
```json
{
  "brand_id": "established-456",
  "financial_capacity": {
    "transaction": 10000000,
    "max_affordable_rent": 5000000
  }
}
```

**Result:**
- System detects positive transaction value
- Applies `max_price = 5,000,000` (from max_affordable_rent)
- Recommends booths with rent_price <= 5,000,000

### Scenario 3: Brand with Zero Transactions

**Input:**
```json
{
  "brand_id": "new-789",
  "financial_capacity": {
    "transaction": 0,
    "max_affordable_rent": 3000000
  }
}
```

**Result:**
- System detects zero (not negative) transaction value
- Applies `max_price = 3,000,000` (from max_affordable_rent)
- Recommends booths with rent_price <= 3,000,000

## Benefits

1. **Startup Support**: Helps new brands find affordable booth options
2. **Financial Alignment**: Ensures recommendations match brand financial capacity
3. **Market Accessibility**: Makes mall spaces more accessible to startups
4. **Configurable**: Easy to adjust threshold based on market conditions
5. **Transparent**: Clear logging helps track startup recommendations

## Future Enhancements

Potential improvements to consider:

1. **Dynamic Thresholds**: Adjust based on mall location or market segment
2. **Graduated Pricing**: Multiple tiers for different startup stages
3. **Negotiation Support**: Flag these brands for special pricing discussions
4. **Growth Tracking**: Monitor when brands graduate from startup status
5. **Regional Variations**: Different thresholds for different geographic areas

## Technical Notes

- The transaction value check happens before max_affordable_rent check
- If transaction is negative, max_affordable_rent is ignored
- The threshold applies to both mall and brand recommendation endpoints
- The logic is centralized in `BoothFilterExtractor` for consistency
- No database schema changes required - uses existing financial_capacity data

## Monitoring

To monitor startup brand recommendations:

1. Check application logs for warning messages about negative transactions
2. Track booth recommendations with price <= STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD
3. Monitor success rate of booth rentals for startup brands
4. Analyze if threshold adjustment is needed based on market feedback

## Support

For questions or issues related to startup brand detection:
- Review logs for startup detection warnings
- Verify brand financial_capacity data is correctly populated
- Check STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD environment variable
- Ensure booth rental prices are accurately maintained in database

