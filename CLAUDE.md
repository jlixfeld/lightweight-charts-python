# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI application that renders TradingView-style OHLC charts using the lightweight-charts JavaScript library. The application serves as a demo for displaying financial market data through a web interface and REST API.

## Architecture

**Application Structure:**
- `app/main.py` - FastAPI application entry point with REST endpoints
- `app/config.py` - Configuration management using Pydantic settings with environment variable support
- `app/schemas.py` - Pydantic models for API request/response validation
- `app/csv_services.py` - CSV data processing services
- `app/database.py` - Database connection and SQLAlchemy models (designed for PostgreSQL but currently using CSV)
- `app/templates/` - Jinja2 HTML templates for chart rendering
- `app/static/` - Static assets for the web interface

**Configuration System:**
The app uses a nested configuration structure via `app/config.py`:
- Main settings in `Settings` class
- Database column mapping in `DatasetConfig` class
- Environment variables use double underscores for nesting (e.g., `DATASET__TABLE`)
- `.env` file support with automatic loading

**Data Flow:**
1. Configuration maps database columns to OHLC schema via environment variables
2. CSV services read data from `/workspace/ohlcv.csv` (hardcoded path in current implementation)
3. FastAPI endpoints serve data to JavaScript chart frontend
4. Templates render interactive charts using lightweight-charts library

## Development Commands

**Local Development:**
```bash
# Install dependencies
pip install -r app/requirements.txt

# Run development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# With environment variables
export DATABASE_URL="sqlite:///demo.db"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Docker Development:**
```bash
# Build image
docker build -f docker/Dockerfile -t charts-web:latest .

# Run with docker-compose
docker compose -f docker/docker-compose.yml up

# Build and run
docker compose -f docker/docker-compose.yml up --build

# Application is ready at http://localhost:9000
```

**Code Quality:**
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Both format and lint
ruff format . && ruff check .
```

## Environment Variables

**Database Configuration:**
- `DATABASE_URL` - SQLAlchemy connection string (currently not used, CSV mode active)
- `OHLC_LIMIT` - Maximum rows per query (default: 500)

**Column Mapping (DATASET__ prefix):**
- `DATASET__TABLE` - Table/view name (default: "ohlc")
- `DATASET__TIME_COLUMN` - Timestamp column (default: "time")
- `DATASET__OPEN_COLUMN`, `DATASET__HIGH_COLUMN`, `DATASET__LOW_COLUMN`, `DATASET__CLOSE_COLUMN` - OHLC price columns
- `DATASET__VOLUME_COLUMN` - Volume column (optional)
- `DATASET__SYMBOL_COLUMN` - Symbol identifier column
- `DATASET__TIMEFRAME_COLUMN` - Timeframe grouping column
- `DATASET__EXTRA_COLUMNS` - Comma-separated additional columns to include

## API Endpoints

- `GET /` - Main page with embedded chart
- `GET /chart` - Chart page with optional symbol/timeframe parameters
- `GET /ohlc` - Returns OHLC data (requires symbol parameter)
- `GET /metadata` - Returns available symbols and timeframes
- `GET /healthz` - Health check endpoint
- `GET /docs` - OpenAPI documentation

## Deployment

**Kubernetes:**
```bash
# Create database secret
kubectl create secret generic lightweight-charts-db-secret \
  --from-literal=DATABASE_URL="postgresql+psycopg2://user:password@db-host:5432/markets"

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Access the chart interface
kubectl port-forward deploy/lightweight-charts-web 9000:8000
```

## Current Implementation Notes

- Application currently operates in CSV mode, reading from hardcoded `/workspace/ohlcv.csv`
- Database functionality exists but is not active in current CSV-based implementation
- Port 8000 is used in containers, mapped to 9000 externally in docker-compose
- Python 3.11+ required (enforced in code)
- Ruff is configured for code formatting and linting with specific rules in `pyproject.toml`