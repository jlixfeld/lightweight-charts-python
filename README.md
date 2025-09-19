# Lightweight Charts Demo

Minimal FastAPI service that renders TradingView-style OHLC charts using the `lightweight-charts` JavaScript bundle. It can read data from either CSV files or PostgreSQL databases and provides a web interface for visualizing financial market data.

## Docker Workflow

```bash
# Build and run using Docker Compose
docker compose -f docker/docker-compose.yml up --build

# Or build manually
docker build -f docker/Dockerfile -t lightweight-charts:latest .
docker compose -f docker/docker-compose.yml up
```

Visit <http://localhost:9000> to browse the chart. The interface includes:
- Interactive chart with OHLC candlesticks
- Searchable symbol picker with real-time filtering
- Timeframe selector
- Inside/outside bar pattern highlighting (enabled by default)

The application reads data from the included sample CSV file (`ohlcv.csv`) containing demo financial data.

## Column Mapping Reference (Database Mode)

When using database mode, all behavior is controlled via environment variables (also respected from an optional `.env`). The app reflects the table/view named by `DATASET__TABLE` and maps the required fields onto your schema. Only the values you set are used—no schema assumptions.

**Note:** These settings are not used in the current CSV mode implementation.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string (use a Secret in Kubernetes). |
| `OHLC_LIMIT` | Maximum rows to return per query (default `500`). |
| `DATASET__TABLE` | Table or view holding OHLC candles. |
| `DATASET__TIME_COLUMN` | Timestamp column. |
| `DATASET__OPEN_COLUMN` / `HIGH` / `LOW` / `CLOSE` | Price columns. |
| `DATASET__VOLUME_COLUMN` | Optional volume column; leave blank to disable. |
| `DATASET__SYMBOL_COLUMN` | Symbol identifier column. |
| `DATASET__TIMEFRAME_COLUMN` | Timeframe/grouping column. |
| `DATASET__EXTRA_COLUMNS` | Comma-separated columns to echo back as metadata. |

Minimum schema requirements: timestamp, open, high, low, close, symbol, timeframe. If `DATASET__VOLUME_COLUMN` is omitted or empty, the volume pane is hidden automatically.

## Kubernetes Deployment

```bash
# store credentials as a secret
kubectl create secret generic lightweight-charts-db-secret \
  --from-literal=DATABASE_URL="postgresql+psycopg2://user:password@db-host:5432/markets"

# adjust env vars in k8s/deployment.yaml as needed, then
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# the pod serves the chart interface
```

Expose the `lightweight-charts-web` service via your preferred ingress/LoadBalancer mechanism. Both `/chart` (HTML) and `/docs` (OpenAPI) are available once the pod is running.

## Available Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Simple frame that embeds `/chart`. |
| GET | `/chart` | Server-rendered HTML chart with searchable symbol picker. |
| GET | `/healthz` | Liveness/readiness probe. |
| GET | `/metadata` | Lists distinct symbols/timeframes + column names. |
| GET | `/ohlc` | Returns candles (`symbol`, optional `timeframe`, optional `limit`). |
| GET | `/docs` | OpenAPI documentation. |

## Data Source Modes

The application supports two data source modes:

### CSV Mode (Default)
The application currently operates in **CSV mode**, reading data from a hardcoded file at `/workspace/ohlcv.csv`. This is the default mode and requires no additional configuration.

**Features:**
- Reads OHLC data directly from CSV files
- No database connection required
- Ideal for demos and simple deployments
- Sample data file included (`ohlcv.csv`)

### Database Mode (Available but Not Active)
The application includes full PostgreSQL database support, but **database mode is not currently active** in the main application code. All database infrastructure exists in the codebase:

- Database models and schemas (`app/models.py`, `app/schemas.py`)
- Database services (`app/services.py`)
- Configuration system (`app/config.py`)

**To use database mode**, you would need to:
1. Have an existing PostgreSQL database with OHLC data in the expected schema
2. Configure the `DATABASE_URL` environment variable
3. Modify `app/main.py` to use database services instead of CSV services

**Note:** The application is designed as a read-only chart viewer. It reads existing data from your database or CSV files but does not write or modify data sources.

## Development

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Node.js 18+ and npm (for JavaScript linting/formatting)

### Quick Start
```bash
# Set up development environment
inv setup

# Start development server
inv dev

# Run tests
inv test

# Run all quality checks
inv check-all
```

### Available Tasks
```bash
# View all available tasks
inv --list

# Get help for specific task
inv <task> --help

# Python development tasks
inv format          # Format Python code with ruff
inv lint --fix      # Lint and auto-fix Python issues
inv typecheck       # Run type checking
inv test --cov      # Run tests with coverage
inv clean           # Clean cache files

# JavaScript development tasks
inv format --js     # Format JS/HTML with prettier
inv lint --js --fix # Lint and auto-fix JS with ESLint
inv js-check        # Run all JS checks
inv js-fix          # Fix all JS issues

# Combined tasks
inv check-all       # Run all Python + JS checks
inv fix-all         # Fix all Python + JS issues

# Docker development
inv docker-up       # Start with docker-compose
inv docker-down     # Stop services
inv docker-logs     # View logs

# Pre-commit hooks
inv precommit --install     # Install hooks
inv precommit --all-files   # Run on all files
```

### Code Quality
The project uses:

**Python:**
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** for testing
- **Bandit** for security scanning

**JavaScript:**
- **ESLint** for linting
- **Prettier** for formatting

**General:**
- **Pre-commit** hooks for automated checks
- **Hadolint** for Dockerfile linting

### Adding Dependencies
```bash
# Add production dependency
inv add package-name

# Add development dependency
inv add package-name --dev

# Remove dependency
inv remove package-name
```

## Python Version

The app requires Python **3.11** or newer (enforced at import time).
