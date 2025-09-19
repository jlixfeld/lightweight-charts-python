import logging
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import schemas
from . import csv_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lightweight Charts Demo")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.get("/ohlc", response_model=list[schemas.OHLC])
def get_ohlc(
    symbol: str = Query(..., description="Symbol identifier"),
    timeframe: str | None = Query(None, description="Timeframe to filter"),
    limit: int | None = Query(None, ge=1, le=50_000),
):
    try:
        return csv_services.list_ohlc_from_csv(
            csv_path="/workspace/ohlcv.csv",
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )
    except Exception as exc:
        logger.error(f"Failed to fetch OHLC for {symbol}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch OHLC data")

@app.get("/metadata", response_model=schemas.Metadata)
def get_metadata():
    try:
        return csv_services.get_metadata_from_csv("/workspace/ohlcv.csv")
    except Exception as exc:
        logger.error(f"Failed to fetch metadata: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch metadata")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chart", response_class=HTMLResponse)
async def chart_page(
    request: Request,
    symbol: str | None = Query(None, description="Optional symbol to preselect"),
    timeframe: str | None = Query(None, description="Optional timeframe to preselect"),
):
    state = csv_services.build_chart_state_from_csv("/workspace/ohlcv.csv", symbol, timeframe)
    return templates.TemplateResponse("chart.html", {"request": request, "state": state})
