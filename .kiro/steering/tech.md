# Technology Stack

## Backend
- **Framework**: FastAPI with Python 3.8+
- **Database**: SQLAlchemy ORM with SQLite (configurable to other databases)
- **AI Integration**: Claude API (Anthropic) for article summarization
- **Web Scraping**: BeautifulSoup4 and newspaper3k
- **Email**: SMTP with configurable providers
- **Server**: Uvicorn ASGI server

## Frontend
- **Static Files**: Vanilla HTML, CSS, JavaScript
- **Testing**: Jest for JavaScript tests

## Key Dependencies
```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
newspaper3k>=0.2.8
```

## Development Commands

### Running the Application
```bash
# Development mode with auto-reload
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run Python tests
pytest

# Run JavaScript tests
npm run test:js

# Run with coverage
pytest --cov=.
```

### Database
```bash
# Initialize database
python init_db.py

# Database is auto-created on first run
```

## Configuration
- Environment variables via `.env` file
- Settings managed through `config.py`
- See `.env.example` for required variables