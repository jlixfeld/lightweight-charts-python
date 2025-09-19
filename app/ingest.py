from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import settings
from .database import SessionLocal, engine
from . import services, schemas


def ingest_csv(path: Path, symbol: str, timeframe: str, description: str | None = None) -> int:
    cfg = settings.dataset

    df = pd.read_csv(path)
    if cfg.time_column not in df.columns and "time" in df.columns:
        df.rename(columns={"time": cfg.time_column}, inplace=True)
    if cfg.open_column not in df.columns and "open" in df.columns:
        df.rename(columns={"open": cfg.open_column}, inplace=True)
    if cfg.high_column not in df.columns and "high" in df.columns:
        df.rename(columns={"high": cfg.high_column}, inplace=True)
    if cfg.low_column not in df.columns and "low" in df.columns:
        df.rename(columns={"low": cfg.low_column}, inplace=True)
    if cfg.close_column not in df.columns and "close" in df.columns:
        df.rename(columns={"close": cfg.close_column}, inplace=True)
    if cfg.volume_column and cfg.volume_column not in df.columns and "volume" in df.columns:
        df.rename(columns={"volume": cfg.volume_column}, inplace=True)

    required = {
        cfg.time_column,
        cfg.open_column,
        cfg.high_column,
        cfg.low_column,
        cfg.close_column,
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    df[cfg.symbol_column] = symbol
    df[cfg.timeframe_column] = timeframe
    df[cfg.time_column] = pd.to_datetime(df[cfg.time_column])

    df.to_sql(cfg.table, engine, if_exists="append", index=False, method="multi")

    with SessionLocal() as session:
        services.create_instrument(
            session,
            schemas.InstrumentCreate(symbol=symbol, description=description),
        )

    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest OHLC CSV data into the database")
    parser.add_argument("csv", type=Path, help="Path to CSV file")
    parser.add_argument("symbol", help="Symbol identifier")
    parser.add_argument("timeframe", help="Timeframe identifier")
    parser.add_argument("--description", help="Instrument description", default=None)

    args = parser.parse_args()
    rows = ingest_csv(args.csv, args.symbol, args.timeframe, args.description)
    print(f"Inserted {rows} rows for symbol={args.symbol} timeframe={args.timeframe}")


if __name__ == "__main__":
    main()
