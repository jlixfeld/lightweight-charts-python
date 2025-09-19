import logging

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from . import csv_services, schemas, services
from .config import settings
from .database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lightweight Charts Demo")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def use_database_mode() -> bool:
    """Determine if we should use database mode based on database availability."""
    try:
        # Test database connection
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.info("Database not available, falling back to CSV mode")
        return False


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}


@app.get("/ohlc", response_model=list[schemas.OHLC])
def get_ohlc(
    symbol: str = Query(..., description="Symbol identifier"),
    timeframe: str | None = Query(None, description="Timeframe to filter"),
    limit: int | None = Query(None, ge=1, le=50_000, description="Number of records to return"),
) -> list[schemas.OHLC]:
    try:
        if use_database_mode():
            with SessionLocal() as db:
                return services.list_ohlc(db, symbol=symbol, timeframe=timeframe, limit=limit)
        else:
            csv_path = "/workspace/ohlcv.csv"
            return csv_services.list_ohlc_from_csv(
                csv_path=csv_path,
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
    except Exception as exc:
        logger.error(f"Failed to fetch OHLC for {symbol}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch OHLC data") from exc


@app.get("/metadata", response_model=schemas.Metadata)
def get_metadata():
    try:
        if use_database_mode():
            with SessionLocal() as db:
                return services.get_metadata(db)
        else:
            csv_path = "/workspace/ohlcv.csv"
            return csv_services.get_metadata_from_csv(csv_path)
    except Exception as exc:
        logger.error(f"Failed to fetch metadata: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata") from exc


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chart", response_class=HTMLResponse)
async def chart_page(
    request: Request,
    symbol: str | None = Query(None, description="Optional symbol to preselect"),
    timeframe: str | None = Query(None, description="Optional timeframe to preselect"),
):
    try:
        if use_database_mode():
            state = services.build_chart_state(symbol, timeframe)
        else:
            csv_path = "/workspace/ohlcv.csv"
            state = csv_services.build_chart_state_from_csv(csv_path, symbol, timeframe)
        return templates.TemplateResponse("chart.html", {"request": request, "state": state})
    except Exception as exc:
        logger.error(f"Failed to build chart state: {exc}")
        # Fallback state for error cases
        error_state = {
            "symbols": [],
            "timeframes": [],
            "activeSymbol": None,
            "activeTimeframe": None,
            "limit": settings.ohlc_limit,
            "volumeEnabled": False,
            "error": str(exc),
        }
        return templates.TemplateResponse("chart.html", {"request": request, "state": error_state})
