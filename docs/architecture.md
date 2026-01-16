# DealFlow AI Copilot - Architecture Documentation

## System Overview

DealFlow AI Copilot is a multi-agent AI system designed to automate private equity deal analysis. The system processes deal documents, extracts relevant information, and generates comprehensive investment insights using Google Gemini.

## Core Components

### 1. FastAPI Application (`app/main.py`)

The main entry point for the API server. Handles:
- Request routing
- CORS configuration
- Middleware setup
- Startup/shutdown events
- Exception handling

### 2. Configuration Management (`app/config.py`)

Pydantic-based settings management:
- Environment variable loading
- Type validation
- Default values
- Path management for data directories

### 3. API Layer (`app/api/`)

RESTful endpoints organized by domain:
- **health.py**: System health and readiness checks
- **deals.py**: Deal document upload and analysis (to be implemented)

### 4. Agent Layer (`app/agents/`)

Multi-agent orchestration for different analysis tasks:

```
+-------------------+
|  Agent Manager    |
|-------------------|
| - Orchestration   |
| - Task Routing    |
| - Result Merge    |
+-------------------+
         |
    +----+----+----+----+
    |    |    |    |    |
    v    v    v    v    v
+-----+ +-----+ +-----+ +-----+ +-----+
|Extr.| |Fin. | |Mkt. | |Risk | |Sum. |
|Agent| |Agent| |Agent| |Agent| |Agent|
+-----+ +-----+ +-----+ +-----+ +-----+
```

#### Planned Agents:

1. **Extraction Agent**
   - Document parsing
   - Data extraction
   - Entity recognition

2. **Financial Analysis Agent**
   - Financial statement analysis
   - Ratio calculations
   - Trend analysis

3. **Market Research Agent**
   - Industry analysis
   - Competitor research
   - Market sizing

4. **Risk Assessment Agent**
   - Risk identification
   - Risk scoring
   - Mitigation suggestions

5. **Summary Agent**
   - Investment memo generation
   - Executive summary
   - Key findings

### 5. Service Layer (`app/services/`)

Business logic and operations:
- Document processing
- Analysis orchestration
- Export generation
- Storage management

### 6. Integration Layer (`app/integrations/`)

External API clients:
- Google Gemini API
- PitchBook API
- Crunchbase API
- SERP API

### 7. Utility Layer (`app/utils/`)

Shared utilities:
- **logger.py**: Loguru configuration
- **exceptions.py**: Custom exception classes

## Data Flow

```
                    Document Upload
                          |
                          v
+------------------+  +------------------+
|  Document Store  |  | File Validation  |
|  (data/uploads)  |  |                  |
+--------+---------+  +--------+---------+
         |                     |
         v                     v
+------------------+  +------------------+
| Document Parser  |  |  OCR Processing  |
| (PyPDF2, docx)   |  |  (if needed)     |
+--------+---------+  +--------+---------+
         |                     |
         +----------+----------+
                    |
                    v
         +------------------+
         | Extraction Agent |
         | (Gemini API)     |
         +--------+---------+
                  |
                  v
         +------------------+
         | Structured Data  |
         | (JSON/Pydantic)  |
         +--------+---------+
                  |
    +-------------+-------------+
    |             |             |
    v             v             v
+-------+   +---------+   +-------+
|Finance|   | Market  |   | Risk  |
| Agent |   | Agent   |   | Agent |
+---+---+   +----+----+   +---+---+
    |            |            |
    +------------+------------+
                 |
                 v
         +------------------+
         |  Summary Agent   |
         | (Memo Generation)|
         +--------+---------+
                  |
                  v
         +------------------+
         |   Output Store   |
         | (data/outputs)   |
         +------------------+
```

## Error Handling

Custom exception hierarchy:

```
DealFlowBaseException
├── ExtractionError     # Document extraction failures
├── AnalysisError       # AI analysis failures
├── ValidationError     # Data validation failures
└── APIError            # External API failures
```

All exceptions include:
- Human-readable message
- Error code for categorization
- Details dictionary for context
- Serialization to JSON for API responses

## Logging Strategy

Using Loguru with dual outputs:
1. **Console**: Colorized INFO+ level for development
2. **File**: DEBUG+ level with rotation (10MB, 7 days)

Log format includes:
- Timestamp
- Level
- Module:function:line
- Message

## Security Considerations

1. **Authentication**: To be implemented (JWT recommended)
2. **API Keys**: Stored in environment variables, never in code
3. **File Upload**: Validation and size limits
4. **CORS**: Currently permissive, restrict in production
5. **Container**: Non-root user in Docker

## Scalability

Current design supports:
- Horizontal scaling via container orchestration
- Async processing with FastAPI/uvicorn
- File-based storage (can migrate to S3/GCS)

Future considerations:
- Redis for caching and job queues
- PostgreSQL for persistent storage
- Celery for background tasks

## Extensibility

The architecture supports easy extension:

1. **New Agents**: Add to `app/agents/`, register with orchestrator
2. **New Integrations**: Add to `app/integrations/`, inject into services
3. **New Endpoints**: Add routers to `app/api/`, include in main app
4. **New Models**: Add schemas to `app/models/`

## Configuration Options

All configuration via environment variables:

| Category | Variables |
|----------|-----------|
| App | APP_NAME, DEBUG |
| AI | GOOGLE_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE |
| External | PITCHBOOK_API_KEY, CRUNCHBASE_API_KEY, SERP_API_KEY |
| Storage | UPLOAD_DIR, PROCESSED_DIR, OUTPUT_DIR |

## Monitoring

Health endpoints for monitoring:
- `/health`: Basic health status
- `/health/ready`: Readiness for traffic
- `/health/live`: Liveness probe

Docker health check configured for container orchestration.

## Future Roadmap

1. **Phase 1** (Current): Core infrastructure
2. **Phase 2**: Document processing and extraction
3. **Phase 3**: AI agent implementation
4. **Phase 4**: External integrations
5. **Phase 5**: Advanced analytics and reporting
