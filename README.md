# DealFlow AI Copilot

AI-powered private equity deal analysis platform with multi-agent orchestration using Google Gemini.

## Overview

DealFlow AI Copilot automates the analysis of private equity deals by extracting data from deal documents (CIMs, financial statements, pitch decks) and leveraging AI agents to generate comprehensive investment insights.

## Features

- **Document Processing**: Extract and parse data from PDFs, Word documents, and images
- **Multi-Agent Analysis**: Orchestrated AI agents for different analysis tasks
- **Financial Analysis**: Automated financial modeling and valuation
- **Market Intelligence**: Integration with PitchBook, Crunchbase, and web search
- **Risk Assessment**: AI-powered risk identification and scoring
- **Investment Memos**: Auto-generated investment memoranda and reports

## Architecture

```
                                    +------------------+
                                    |   Client Apps    |
                                    | (Web/Mobile/CLI) |
                                    +--------+---------+
                                             |
                                             v
+------------------------------------------------------------------------------------+
|                              FastAPI Application                                    |
|                                                                                    |
|  +-------------+  +-------------+  +-------------+  +-------------+               |
|  |   /health   |  |   /deals    |  |  /analysis  |  |   /export   |               |
|  +-------------+  +-------------+  +-------------+  +-------------+               |
|                                                                                    |
+------------------------------------------------------------------------------------+
                                             |
              +------------------------------+------------------------------+
              |                              |                              |
              v                              v                              v
+-------------------+          +-------------------+          +-------------------+
|  Document Service |          |  Analysis Service |          |   Export Service  |
|                   |          |                   |          |                   |
| - PDF Extraction  |          | - Agent Orchestr. |          | - PDF Generation  |
| - Text Parsing    |          | - Result Aggreg.  |          | - Excel Export    |
| - OCR Processing  |          | - Caching         |          | - Memo Templates  |
+-------------------+          +-------------------+          +-------------------+
              |                              |
              v                              v
+-------------------+          +-------------------------------------------+
|   File Storage    |          |              AI Agents                    |
|                   |          |                                           |
| - data/uploads    |          | +----------+ +----------+ +----------+   |
| - data/processed  |          | |Extraction| | Analysis | | Research |   |
| - data/outputs    |          | |  Agent   | |  Agent   | |  Agent   |   |
+-------------------+          | +----------+ +----------+ +----------+   |
                               |                                           |
                               +-------------------------------------------+
                                             |
              +------------------------------+------------------------------+
              |                              |                              |
              v                              v                              v
+-------------------+          +-------------------+          +-------------------+
|   Google Gemini   |          |    PitchBook API  |          |  Crunchbase API   |
|       API         |          |                   |          |                   |
+-------------------+          +-------------------+          +-------------------+
```

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.109.0 |
| Language | Python 3.11+ |
| AI/ML | Google Gemini (gemini-1.5-pro) |
| Document Processing | PyPDF2, pdf2image, python-docx |
| Data Processing | Pandas |
| HTTP Client | httpx (async) |
| Logging | Loguru |
| Configuration | Pydantic Settings |
| Testing | pytest, pytest-asyncio |
| Containerization | Docker |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Google API key for Gemini
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/dealflow-ai-copilot.git
   cd dealflow-ai-copilot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Verify setup**
   ```bash
   python scripts/test_setup.py
   ```

6. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t dealflow-ai-copilot .
docker run -p 8000:8000 --env-file .env dealflow-ai-copilot
```

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check |
| GET | `/health/live` | Liveness check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

### Deals API (Coming Soon)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/deals/upload` | Upload deal documents |
| POST | `/api/v1/deals/analyze` | Start deal analysis |
| GET | `/api/v1/deals/{deal_id}` | Get deal details |
| GET | `/api/v1/deals/{deal_id}/analysis` | Get analysis results |
| GET | `/api/v1/deals` | List all deals |
| DELETE | `/api/v1/deals/{deal_id}` | Delete a deal |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | DealFlow AI Copilot |
| `DEBUG` | Enable debug mode | False |
| `GOOGLE_API_KEY` | Google Gemini API key | (required) |
| `PITCHBOOK_API_KEY` | PitchBook API key | (optional) |
| `CRUNCHBASE_API_KEY` | Crunchbase API key | (optional) |
| `SERP_API_KEY` | SERP API key | (optional) |
| `UPLOAD_DIR` | Upload directory | data/uploads |
| `PROCESSED_DIR` | Processed files directory | data/processed |
| `OUTPUT_DIR` | Output directory | data/outputs |
| `DEFAULT_MODEL` | Default Gemini model | gemini-1.5-pro-latest |
| `DEFAULT_TEMPERATURE` | AI temperature | 0.3 |
| `MAX_TOKENS` | Max tokens per response | 2048 |

## Project Structure

```
dealflow-ai-copilot/
├── app/
│   ├── __init__.py          # Package init with version
│   ├── main.py              # FastAPI application
│   ├── config.py            # Pydantic settings
│   ├── api/                 # API routers
│   │   ├── health.py        # Health check endpoints
│   │   └── deals.py         # Deal endpoints (placeholder)
│   ├── agents/              # AI agent implementations
│   ├── core/                # Core business logic
│   ├── integrations/        # External API clients
│   ├── models/              # Pydantic schemas
│   ├── services/            # Business services
│   └── utils/               # Utilities
│       ├── logger.py        # Loguru configuration
│       └── exceptions.py    # Custom exceptions
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
│   └── test_setup.py        # Setup validation
├── docs/                    # Documentation
├── data/                    # Data directories
│   ├── uploads/             # Uploaded files
│   ├── processed/           # Processed documents
│   └── outputs/             # Analysis outputs
├── prompts/                 # AI prompt templates
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container definition
└── docker-compose.yml      # Container orchestration
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_health.py
```

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint code
ruff check app tests

# Type checking
mypy app
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Google Gemini](https://ai.google.dev/) - AI model provider
- [Loguru](https://github.com/Delgan/loguru) - Python logging made simple
