# Lightweight Charts Demo

Minimal FastAPI service that renders TradingView-style OHLC charts using the `lightweight-charts` JavaScript bundle. It expects an existing PostgreSQL database with candle data and exposes both HTML and REST endpoints for interacting with that dataset.

## Docker Workflow

```bash
# run from repository root
# configure connection details (or place them in .env)
export DATABASE_URL="postgresql+psycopg2://user:password@db-host:5432/markets"
export DATASET__TABLE=ohlc
export DATASET__TIME_COLUMN=time
export DATASET__OPEN_COLUMN=open
export DATASET__HIGH_COLUMN=high
export DATASET__LOW_COLUMN=low
export DATASET__CLOSE_COLUMN=close
export DATASET__VOLUME_COLUMN=volume
export DATASET__SYMBOL_COLUMN=symbol
export DATASET__TIMEFRAME_COLUMN=timeframe
export DATASET__EXTRA_COLUMNS="rsi,atr"

# build and run (docker/Dockerfile and docker/docker-compose.yml)
docker build -f docker/Dockerfile -t charts-web:latest .
docker compose -f docker/docker-compose.yml up

# optional CSV ingestion once the container is running (sample ohlcv.csv provided)
docker compose -f docker/docker-compose.yml exec web \
  python -m app.ingest ohlcv.csv AAPL 1D --description "Apple daily"
```

Visit <http://localhost:8000> to browse the chart. The top bar discovers symbols/timeframes dynamically from the configured columns.

## Column Mapping Reference

All behaviour is controlled via environment variables (also respected from an optional `.env`). At startup the app reflects the table/view named by `DATASET__TABLE` and maps the required fields onto your schema. Only the values you set are used—no schema assumptions.

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
kubectl create secret generic lwc-db-secret \
  --from-literal=DATABASE_URL="postgresql+psycopg2://user:password@db-host:5432/markets"

# adjust env vars in k8s/deployment.yaml as needed, then
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# load additional data later if needed
kubectl exec -it deploy/lwc-web -- python -m app.ingest ohlcv.csv AAPL 1D
```

Expose the `lwc-web` service via your preferred ingress/LoadBalancer mechanism. Both `/chart` (HTML) and `/docs` (OpenAPI) are available once the pod is running.

## Available Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Simple frame that embeds `/chart`. |
| GET | `/chart` | Server-rendered HTML chart. |
| GET | `/healthz` | Liveness/readiness probe. |
| GET | `/metadata` | Lists distinct symbols/timeframes + column names. |
| GET | `/ohlc` | Returns candles (`symbol`, optional `timeframe`, optional `limit`). |
| POST | `/instruments` | Register instrument metadata. |
| POST | `/ohlc` | Insert individual candles (expects instrument to exist). |

## Python Version

The app requires Python **3.11** or newer (enforced at import time).
