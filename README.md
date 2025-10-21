# IBM Watsonx Banking Data Cleaning Pipeline

AI-powered data validation and cleaning pipeline for banking datasets using IBM Watsonx Orchestrate.

## Tech Stack

- **Frontend**: Angular 17+, TypeScript, Angular Material
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Orchestration**: IBM Watsonx Orchestrate
- **Database**: PostgreSQL 15+
- **AI/ML**: Watsonx.ai, LangChain
- **Deployment**: Docker, IBM Cloud

## Project Structure

```
IBMCapstone/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── watsonx/           # Watsonx integration
│   │   └── config.py          # Configuration
│   ├── tests/                 # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # UI components
│   │   │   ├── services/      # API services
│   │   │   └── models/        # TypeScript models
│   │   └── environments/
│   ├── angular.json
│   └── package.json
├── watsonx/                    # Watsonx Orchestrate configs
│   ├── nodes/                 # Individual node definitions
│   ├── pipelines/             # Pipeline configurations
│   └── skills/                # Custom skills
├── database/                   # Database scripts
│   ├── migrations/            # SQL migrations
│   └── schema.sql             # Database schema
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose
- IBM Cloud account with Watsonx access

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IBMCapstone
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your credentials
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Or run locally:**

   **Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm install
   ng serve
   ```

   **Database:**
   ```bash
   psql -U postgres -d banking_pipeline -f database/schema.sql
   ```

## API Endpoints

- `POST /api/v1/ingest` - Upload raw banking data
- `GET /api/v1/pipelines/{id}` - Get pipeline execution status
- `GET /api/v1/metrics` - Retrieve cleaning metrics
- `GET /api/v1/datasets` - List processed datasets
- `GET /api/v1/anomalies` - Get detected anomalies

## Watsonx Orchestrate Nodes

1. **Data Ingestion Node** - Ingests CSV, SQL, API data sources
2. **Schema Validator Node** - Validates banking schema compliance
3. **Cleaning Node** - Data normalization and imputation
4. **Anomaly Detector Node** - AI-powered anomaly detection
5. **Review & Feedback Node** - Logging and metrics collection
6. **Publishing Node** - Writes validated data to PostgreSQL

## Features

- Real-time data validation pipeline
- AI-powered anomaly detection using Watsonx.ai
- Interactive dashboard for metrics visualization
- Row-level metadata tracking
- Automated data quality scoring
- Multi-source data ingestion (CSV, SQL, REST APIs)

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## License

MIT
