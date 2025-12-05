# Environment Variables

This document lists all environment variables used by the Python Recommendation System.

## Database Configuration

```env
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_SCHEMA=platform_service
```

## Redis Configuration

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Elasticsearch Configuration

```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_PROTOCOL=http
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_API_KEY=
ELASTICSEARCH_CA_CERTS=
ELASTICSEARCH_CERT_FINGERPRINT=
```

## JWT Configuration

```env
JWT_SECRET=mySecretKey123456789012345678901234567890
JWT_EXPIRATION=86400
JWT_REFRESH_EXPIRATION=604800
JWT_ISSUER=platform-service
```

## Gemini AI Configuration

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
```

## Recommendation System Configuration

### Startup Booth Price Threshold

Used to filter booth recommendations for startup brands with negative transaction values.

```env
STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD=2000000
```

**Description:**
When a brand has a negative transaction value (indicating a startup with low financial capacity), the system will only recommend booths with a rental price below this threshold.

**Default Value:** 2,000,000 (2 million)

**Use Cases:**
- Helps startups find affordable booth options
- Ensures financial alignment for new brands
- Configurable based on market conditions

**Related Documentation:** See `STARTUP_BRAND_LOGIC.md` for detailed information about startup brand detection and recommendation logic.

## Example .env File

Create a `.env` file in the project root with the following content:

```env
DB_USERNAME=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
DB_NAME=platform_db
DB_SCHEMA=platform_service

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_PROTOCOL=http

JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRATION=86400
JWT_REFRESH_EXPIRATION=604800
JWT_ISSUER=platform-service

GEMINI_API_KEY=your_gemini_api_key_here

STARTUP_CHEAP_BOOTH_PRICE_THRESHOLD=2000000
```

## Loading Environment Variables

The application automatically loads environment variables from the `.env` file using `python-dotenv`. Make sure your `.env` file is in the project root directory and is listed in `.gitignore` to prevent committing sensitive information.

## Validation

The application will validate required environment variables on startup and raise an error if critical variables are missing:
- Database configuration variables are required
- Other variables have sensible defaults if not provided

