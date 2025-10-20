# Mall-Business Recommendation System

A comprehensive recommendation system that matches malls with businesses using AI-powered analysis, demographic data, and traffic patterns. The system includes both REST API endpoints and MCP (Model Context Protocol) server integration with Google Gemini AI.

## 🏗️ Architecture

```
app/
├── config/          # Database and Redis configuration
├── datastore/       # Data extraction and caching
├── exception/       # Custom exceptions
├── model/           # Database models (SQLAlchemy)
├── rest/            # REST API endpoints (FastAPI)
├── service/         # Business logic and recommendation algorithms
└── utils/           # Utility functions

mcp-server/
├── mcp_server.py    # MCP server for Gemini AI integration
├── config.py        # Security and database configuration
└── security.py      # SQL injection prevention and validation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Redis server
- Google Gemini API key (optional, for AI features)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd python-recommendation-system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/recommendation_db

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Gemini API Configuration (Optional - for AI features)
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
```

#### Getting a Gemini API Key (Optional)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy and add it to your `.env` file

### 5. Database Setup

Ensure your PostgreSQL database is running and create the required tables:

```sql
-- Create database
CREATE DATABASE recommendation_db;

-- The application will create tables automatically on first run
```

### 6. Redis Setup

Ensure Redis server is running:

```bash
# On Windows (if using Redis for Windows)
redis-server

# On macOS (using Homebrew)
brew services start redis

# On Ubuntu/Debian
sudo systemctl start redis-server
```

## 🏃‍♂️ Running the Application

### Option 1: Run FastAPI Server

```bash
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Run the FastAPI server
python app\app.py
```

The server will start on `http://localhost:8000`

### Option 2: Run with Uvicorn

```bash
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Run with uvicorn directly
uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Run MCP Server (Standalone)

```bash
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Run the MCP server
python mcp-server\mcp_server.py
```

## 📚 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Core Endpoints

#### 🏢 Recommendations
- `GET /recommendations` - Get top N mall-business matches
- `GET /recommendations/mall/{mall_id}` - Get business matches for specific mall
- `GET /recommendations/business/{business_id}` - Get mall matches for specific business

#### 🧠 AI-Powered Queries (MCP Integration)
- `POST /mcp/query-malls` - Query mall database using natural language
- `GET /mcp/tools` - Get available MCP tools
- `GET /mcp/status` - Check MCP server status

#### 💾 Cache Management
- `POST /cache/demographics` - Calculate and cache demographics
- `GET /cache/status` - Check cache status

### Example API Usage

```bash
# Get top 10 recommendations
curl "http://localhost:8000/recommendations?limit=10"

# Query malls using natural language (AI)
curl -X POST "http://localhost:8000/mcp/query-malls" \
  -H "Content-Type: application/json" \
  -d '{"message": "Find malls in District 1 with rent under $1000"}'

# Check system health
curl "http://localhost:8000/health"
```

## 🔐 Security Features

### Multi-Layer Security
1. **App-level Input Validation** (`app/service/input_validator.py`)
   - Message sanitization
   - Blocked keyword detection
   - Sensitive information filtering
   - Query relevance checking

2. **MCP Server Security** (`mcp-server/security.py`)
   - SQL injection prevention
   - Parameterized queries
   - Database field validation
   - Response sanitization

### Security Configuration
- All database queries use parameterized statements
- Input validation prevents malicious content
- API key management for external services
- Response data sanitization

## 🔧 Development

### Project Structure Guidelines

- **No .bat or .ps1 files** - Use Python scripts only
- **Virtual environment required** - Always run in `.venv`
- **No emojis in logging** - Keep logs clean and professional
- **Minimal comments** - Code should be self-documenting

### Adding Dependencies

```bash
# Install new package
pip install package-name

# Add to requirements.txt
pip freeze > requirements.txt
```

### Running Tests

```bash
# Run tests (if test files exist)
python -m pytest

# Run specific test file
python -m pytest tests/test_example.py
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Database Connection Issues
- Check PostgreSQL is running
- Verify database credentials in `.env`
- Ensure database exists

#### 3. Redis Connection Issues
- Check Redis server is running
- Verify Redis configuration in `.env`

#### 4. MCP Server Issues
- Ensure Gemini API key is valid
- Check internet connection for API calls
- Verify MCP server dependencies are installed

#### 5. Port Already in Use
```bash
# Kill process using port 8000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Logs and Debugging

```bash
# Run with debug logging
python app\app.py --log-level debug

# Check application logs
# Logs are printed to console by default
```

## 📊 Data Models

The system includes models for:
- **Malls**: Location, pricing, visitor traffic
- **Businesses**: Type, budget requirements, demographics
- **Recommendations**: Compatibility scores and matches

## 🤝 Contributing

1. Ensure virtual environment is activated
2. Install dependencies with `pip install -r requirements.txt`
3. Follow the project coding guidelines
4. Test your changes before submitting
5. Update documentation if needed

## 📄 License

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check application logs for error details
4. [Create an issue in the repository]

---

**Note**: This system is designed for development and testing. For production deployment, additional configuration for security, performance, and monitoring may be required.