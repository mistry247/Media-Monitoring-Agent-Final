# Project Structure

## Architecture Pattern
- **Layered Architecture**: Clear separation between API, services, models, and data layers
- **Dependency Injection**: FastAPI's dependency system for database sessions
- **Service Layer**: Business logic encapsulated in service classes
- **Repository Pattern**: Database operations abstracted through SQLAlchemy models

## Directory Organization

```
├── api/                    # FastAPI route handlers
│   ├── articles.py         # Article submission endpoints
│   └── reports.py          # Report generation endpoints
├── models/                 # Pydantic models for validation
│   ├── article.py          # Article data models
│   └── report.py           # Report data models
├── services/               # Business logic layer
│   ├── article_service.py  # Article operations
│   ├── ai_service.py       # Claude AI integration
│   ├── scraping_service.py # Web scraping logic
│   ├── email_service.py    # Email functionality
│   └── report_service.py   # Report generation
├── utils/                  # Shared utilities
│   ├── error_handlers.py   # Error handling and responses
│   ├── logging_config.py   # Logging configuration
│   └── health_check.py     # Health monitoring
├── static/                 # Frontend assets
│   ├── index.html          # Main web interface
│   ├── app.js              # Frontend JavaScript
│   └── styles.css          # Styling
├── tests/                  # Test suite
│   ├── test_*.py           # Python tests (pytest)
│   └── test_frontend.js    # JavaScript tests (Jest)
├── main.py                 # FastAPI application entry point
├── database.py             # SQLAlchemy models and DB config
├── config.py               # Configuration management
└── init_db.py              # Database initialization
```

## Key Conventions

### File Naming
- Snake_case for Python files and modules
- Descriptive names indicating purpose (e.g., `article_service.py`)
- Test files prefixed with `test_`

### Database Models
- SQLAlchemy models in `database.py`
- Pydantic models in `models/` for API validation
- Clear separation between DB and API models

### Error Handling
- Custom exception classes in `utils/error_handlers.py`
- Consistent error response format
- Comprehensive logging with request tracking

### Testing
- Pytest for Python backend tests
- Jest for JavaScript frontend tests
- Test database isolation using fixtures
- Comprehensive test coverage for services and APIs