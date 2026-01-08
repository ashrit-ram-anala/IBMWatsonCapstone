# IBM Watsonx Banking Data Cleaning Pipeline

AI-powered data validation and cleaning pipeline for banking datasets using IBM Watsonx Orchestrate.
- App no longer live - Watsonx Orchestrate license needed for production app and local usage
<img width="1440" height="599" alt="Screenshot 2025-11-28 at 11 18 22 PM" src="https://github.com/user-attachments/assets/bb436b64-20dc-4408-99d4-2e3bdc5a611a" />

## Features

- Real-time data validation and cleaning
- AI-powered anomaly detection using Watsonx.ai
- Interactive dashboard for monitoring pipeline metrics
- Support for multiple data sources (CSV, SQL, API)
- Comprehensive data quality reporting

## Tech Stack

- **Frontend**: Angular, TypeScript, Angular Material
- **Backend**: Python, FastAPI, SQLAlchemy
- **Orchestration**: IBM Watsonx Orchestrate
- **Database**: PostgreSQL
- **AI/ML**: Watsonx.ai, LangChain

## Project Structure

```
IBMCapstone/
├── backend/                   # Python FastAPI backend
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
├── frontend/                  # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # UI components
│   │   │   ├── services/      # API services
│   │   │   └── models/        # TypeScript models
│   │   └── environments/
│   ├── angular.json
│   └── package.json
├── watsonx/                   # Watsonx Orchestrate configs
│   ├── nodes/                 # Individual node definitions
│   ├── pipelines/             # Pipeline configurations
│   └── skills/                # Custom skills
├── database/                  # Database scripts
│   ├── migrations/            # SQL migrations
│   └── schema.sql             # Database schema
├── docker-compose.yml
└── README.md
```

## Quick Start

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IBMCapstone
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
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
   source venv/bin/activate
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

## Watsonx Orchestrate Nodes

1. **Data Ingestion Node** - Ingests CSV, SQL, API data sources
2. **Schema Validator Node** - Validates banking schema compliance
3. **Cleaning Node** - Data normalization and imputation
4. **Anomaly Detector Node** - AI-powered anomaly detection
5. **Review & Feedback Node** - Logging and metrics collection
6. **Publishing Node** - Writes validated data to PostgreSQL
