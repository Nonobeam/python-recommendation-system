# Database Indexes for Booth Recommendations

This document describes the recommended database indexes to optimize booth recommendation queries.

## Required Indexes

### 1. Booth Table Indexes

#### Composite Index for Filtering
```sql
CREATE INDEX idx_booth_available_category_size 
ON platform_service.booth(is_available, zone_id, size_m2) 
WHERE is_available = true;
```

**Purpose:** Optimizes queries that filter by availability, category (via zone), and size range.

#### Mall-based Query Index
```sql
CREATE INDEX idx_booth_mall_available 
ON platform_service.booth(mall_id, is_available) 
WHERE is_available = true;
```

**Purpose:** Optimizes queries that fetch available booths for specific malls.

### 2. Booth Information Table Index

```sql
CREATE INDEX idx_booth_information_booth_id 
ON platform_service.booth_information(booth_id);
```

**Purpose:** Optimizes joins between booth and booth_information tables.

### 3. Booth Rental Price Table Index

```sql
CREATE INDEX idx_booth_rental_price_booth_current 
ON platform_service.booth_rental_price(booth_id, is_current) 
WHERE is_current = true;
```

**Purpose:** Optimizes lookups for current rental prices of booths.

### 4. Zone Table Index (if needed)

```sql
CREATE INDEX idx_zone_categories_id 
ON platform_service.zone(categories_id);
```

**Purpose:** Optimizes category filtering via zone joins.

### 5. Floor Table Index (if needed)

```sql
CREATE INDEX idx_floor_level 
ON platform_service.floor(level);
```

**Purpose:** Optimizes floor level filtering.

## Implementation Notes

- All indexes use partial indexes (WHERE clauses) where applicable to reduce index size
- Indexes are created on the `platform_service` schema
- Consider index maintenance overhead when creating multiple indexes
- Monitor query performance after index creation to verify improvements

## Migration Script

To create all indexes at once:

```sql
-- Booth filtering index
CREATE INDEX IF NOT EXISTS idx_booth_available_category_size 
ON platform_service.booth(is_available, zone_id, size_m2) 
WHERE is_available = true;

-- Mall-based query index
CREATE INDEX IF NOT EXISTS idx_booth_mall_available 
ON platform_service.booth(mall_id, is_available) 
WHERE is_available = true;

-- Booth information index
CREATE INDEX IF NOT EXISTS idx_booth_information_booth_id 
ON platform_service.booth_information(booth_id);

-- Booth rental price index
CREATE INDEX IF NOT EXISTS idx_booth_rental_price_booth_current 
ON platform_service.booth_rental_price(booth_id, is_current) 
WHERE is_current = true;

-- Zone category index
CREATE INDEX IF NOT EXISTS idx_zone_categories_id 
ON platform_service.zone(categories_id);

-- Floor level index
CREATE INDEX IF NOT EXISTS idx_floor_level 
ON platform_service.floor(level);
```

