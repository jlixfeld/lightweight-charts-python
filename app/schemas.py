from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Instrument(BaseModel):
    id: int
    symbol: str
    description: str | None = None

    model_config = {"from_attributes": True}


class InstrumentCreate(BaseModel):
    symbol: str
    description: str | None = None


class OHLC(BaseModel):
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    extra: dict | None = None


class OHLCCreate(BaseModel):
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    extra: dict | None = None


class Metadata(BaseModel):
    symbols: list[str]
    timeframes: list[str]
    columns: list[str]
