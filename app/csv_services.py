from pathlib import Path

import pandas as pd

from . import schemas
from .config import settings
from .utils import sort_timeframes_chronologically


def load_csv_data(csv_path: str = "ohlcv.csv") -> pd.DataFrame:
    """Load OHLC data from CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(path, parse_dates=["time"] if Path(csv_path).exists() else [])
    except Exception as exc:
        raise ValueError(f"Error reading CSV file {csv_path}: {exc}") from exc

    # Add default symbol and timeframe if not present
    if "symbol" not in df.columns:
        df["symbol"] = "DEMO"
    if "timeframe" not in df.columns:
        df["timeframe"] = "1D"

    return df


def list_ohlc_from_csv(
    csv_path: str = "ohlcv.csv",
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int | None = None,
) -> list[schemas.OHLC]:
    """Load OHLC data from CSV file."""
    df = load_csv_data(csv_path)

    # Filter by symbol if provided
    if symbol:
        df = df[df["symbol"] == symbol]

    # Filter by timeframe if provided
    if timeframe:
        df = df[df["timeframe"] == timeframe]

    # Apply limit (0 means unlimited)
    if settings.ohlc_limit == 0:
        limit_value = limit if limit else 0
    else:
        limit_value = min(limit or settings.ohlc_limit, settings.ohlc_limit)

    if limit_value > 0:
        df = df.head(limit_value)

    # Convert to OHLC schema objects
    ohlc_data = []
    for _, row in df.iterrows():
        ohlc_data.append(
            schemas.OHLC(
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                time=row["time"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=(float(row["volume"]) if "volume" in row and pd.notna(row["volume"]) else None),
                extra=None,
            )
        )

    return ohlc_data


def get_metadata_from_csv(csv_path: str = "ohlcv.csv") -> schemas.Metadata:
    """Get metadata from CSV file."""
    df = load_csv_data(csv_path)

    symbols = sorted(df["symbol"].unique().tolist())
    timeframes = sort_timeframes_chronologically(df["timeframe"].unique().tolist())
    columns = df.columns.tolist()

    return schemas.Metadata(symbols=symbols, timeframes=timeframes, columns=columns)


def build_chart_state_from_csv(
    csv_path: str = "ohlcv.csv",
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict:
    """Build chart state from CSV data."""
    try:
        metadata = get_metadata_from_csv(csv_path)
    except FileNotFoundError as exc:
        return {
            "symbols": [],
            "timeframes": [],
            "activeSymbol": None,
            "activeTimeframe": None,
            "limit": settings.ohlc_limit,
            "volumeEnabled": True,
            "error": str(exc),
        }

    available_symbols = metadata.symbols
    timeframes = [tf for tf in metadata.timeframes if tf]

    active_symbol = (
        symbol if symbol and symbol in available_symbols else (available_symbols[0] if available_symbols else None)
    )
    active_timeframe = None if not timeframes else timeframe if timeframe in timeframes else timeframes[0]

    return {
        "symbols": available_symbols,
        "timeframes": timeframes,
        "activeSymbol": active_symbol,
        "activeTimeframe": active_timeframe,
        "limit": settings.ohlc_limit,
        "volumeEnabled": "volume" in metadata.columns,
        "error": None,
    }
